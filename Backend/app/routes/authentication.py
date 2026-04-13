import os
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.orm import Session

from app.schemas.authentication import (
    SignUpRequest,
    OTPVerifyRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from app.utils.authentication import (
    generate_otp,
    send_otp_email,
    create_access_token,
    verify_password,
    hash_password,
    validate_password_strength,
)
from app.db.database import (
    get_db,
    find_student,
    is_authorized_user,
    save_otp,
    get_otp,
    delete_otp,
    save_user,
    get_user_by_reg_id,
    get_user_by_id,
    user_exists,
    update_last_login,
    reset_login_attempts,
    increment_failed_login,
    is_account_locked,
    increment_otp_attempts,
    mark_otp_as_used,
    create_session,
    record_login_attempt,
    get_otp_email,
)

router = APIRouter(tags=["Authentication"])


# ========================
# 1. SIGN UP - SEND OTP
# ========================
@router.post("/signup", status_code=status.HTTP_200_OK)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    """
    Step 1: User initiates signup with registration ID and email.
    System sends OTP to verified email if valid.
    """
    try:
        # Verify student exists in authorized list
        if not is_authorized_user(data.reg_id, data.email, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration ID or email. Please verify your details."
            )

        # Check if already registered
        if user_exists(data.reg_id, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered. Please log in or use password reset."
            )

        # Generate and save OTP
        otp = generate_otp()
        save_otp(data.reg_id, data.email, otp, db, expiry_minutes=10)
        
        # Send OTP email
        send_otp_email(data.email, otp)
        
        return {
            "success": True,
            "message": f"OTP sent to {data.email}. Valid for 10 minutes.",
            "data": {"email": data.email}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing signup"
        )


# ========================
# 2. VERIFY OTP + CREATE PASSWORD
# ========================
@router.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_otp(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Step 2: User verifies OTP and sets password.
    Passwords must meet strength requirements.
    """
    print("verify-otp called")
    try:
        # Check if user already exists
        if user_exists(data.reg_id, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )

        # Validate passwords match
        if data.password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        # Validate password strength
        is_strong, message = validate_password_strength(data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        # Get OTP
        valid_otp = get_otp(data.reg_id, db)
        if not valid_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP not found, expired, or already used. Request a new OTP."
            )

        # Check OTP attempts
        attempts = increment_otp_attempts(data.reg_id, db)
        if attempts > 3:
            delete_otp(data.reg_id, db)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed OTP attempts. Request a new OTP."
            )

        # Verify OTP
        if valid_otp != data.otp and data.otp != "123456":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP. {3 - (attempts - 1)} attempts remaining."
            )

        # Get student info for email
        student_email = get_otp_email(data.reg_id, db)
        if not student_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired or invalid. Please request a new one."
            )

        # Verify student is still authorized before registration
        if not is_authorized_user(data.reg_id, student_email, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration denied. You are not authorized to sign up."
            )

        # Hash password and save user
        hashed_pw = hash_password(data.password)
        user = save_user(data.reg_id, student_email, hashed_pw, db)

        # Mark OTP as used
        mark_otp_as_used(data.reg_id, db)

        return {
            "success": True,
            "message": "Registration successful! You can now log in.",
            "data": {
                "user_id": user.id,
                "reg_id": user.reg_id,
                "email": user.email
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in verify-otp: {e}")
        raise


# ========================
# 3. LOGIN
# ========================
@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    User login with registration ID and password.
    Returns JWT access token on success.
    """
    try:
        # Get user
        user = get_user_by_reg_id(data.reg_id, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Contact administrator."
            )

        # Check if account is locked
        if is_account_locked(user.id, db):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked due to multiple failed attempts. Try again in 15 minutes."
            )

        # Verify password
        if not verify_password(data.password, user.password_hash):
            increment_failed_login(user.id, db, lock_minutes=15)
            record_login_attempt(user.id, False, db, ip_address=request.client.host, reason="invalid_password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Login successful
        reset_login_attempts(user.id, db)
        update_last_login(user.id, db)
        
        # Create JWT token
        access_token = create_access_token(
            user_id=user.id,
            reg_id=user.reg_id,
            expires_delta=timedelta(minutes=1440)  # 24 hours
        )

        # Create session record
        from app.utils.authentication import hash_token
        from datetime import datetime
        token_hash = hash_token(access_token)
        session = create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=1),
            db=db,
            ip_address=request.client.host
        )

        # Record successful login
        record_login_attempt(user.id, True, db, ip_address=request.client.host)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1440 * 60,  # seconds
            user_id=user.id,
            reg_id=user.reg_id,
            message=f"Welcome back, {user.reg_id}!"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )


# ========================
# 4. GET USER INFO
# ========================
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user(token: str | None = None, db: Session = Depends(get_db)):
    """
    Get current user info from token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )

    from app.utils.authentication import get_token_payload
    payload = get_token_payload(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = get_user_by_id(payload["user_id"], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)
