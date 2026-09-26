import logging
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, status, Request, Form
from sqlalchemy.orm import Session

from app.schemas.authentication import (
    SignUpRequest,
    OTPVerifyRequest,
    LoginRequest,
    LoginResponse,
    OAuthTokenResponse,
    UserResponse,
)
from app.utils.authentication import (
    generate_otp,
    send_otp_email,
    create_access_token,
    verify_password,
    hash_password,
    hash_otp,
    hash_token,
    get_token_payload,
    extract_bearer_token,
    verify_otp_value,
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
    get_session_by_token_hash,
)
from app.core.config import settings

router = APIRouter(tags=["Authentication"])
logger = logging.getLogger(__name__)
OAUTH_SCOPES = "student.profile.read student.academic.read student.financial.read"


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
        save_otp(data.reg_id, data.email, hash_otp(otp), db, expiry_minutes=10)
        
        # Send OTP email
        send_otp_email(data.email, otp)
        
        return {
            "success": True,
            "message": f"OTP sent to {data.email}. Valid for 10 minutes.",
            "data": {"email": data.email}
        }
    
    except HTTPException:
        raise
    except Exception:
        logger.exception("Signup processing failed")
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
        if not verify_otp_value(data.otp, valid_otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP. {max(0, 3 - attempts)} attempts remaining."
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
    except Exception:
        logger.exception("OTP verification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying OTP",
        )


# ========================
# 3. LOGIN
# ========================
@router.post("/oauth/token", response_model=OAuthTokenResponse, tags=["OAuth 2.0"])
def oauth_token(
    grant_type: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    scope: str = Form(default=""),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Issue a short-lived scoped bearer token for local OAuth migration."""
    if not settings.ALLOW_LOCAL_OAUTH:
        raise HTTPException(status_code=404, detail="OAuth token endpoint is disabled")
    if grant_type != "password":
        raise HTTPException(status_code=400, detail="Only grant_type=password is supported")

    user = get_user_by_reg_id(username.upper(), db)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_scopes = set(OAUTH_SCOPES.split())
    requested_scopes = set(scope.split()) if scope else allowed_scopes
    if not requested_scopes.issubset(allowed_scopes):
        raise HTTPException(status_code=400, detail="Requested scope is not allowed")

    access_token = create_access_token(
        user_id=user.id,
        reg_id=user.reg_id,
        expires_delta=timedelta(minutes=15),
        scopes=sorted(requested_scopes),
    )
    from datetime import datetime
    create_session(
        user_id=user.id,
        token_hash=hash_token(access_token),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        db=db,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return OAuthTokenResponse(
        access_token=access_token,
        expires_in=15 * 60,
        scope=" ".join(sorted(requested_scopes)),
    )


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    User login with registration ID and password.
    Returns JWT access token on success.
    """
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local login is disabled; use the configured OAuth provider",
        )
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
            record_login_attempt(
                user.id,
                False,
                db,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                reason="invalid_password",
            )
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
            expires_delta=timedelta(minutes=1440),  # 24 hours
            scopes=OAUTH_SCOPES.split(),
        )

        # Create session record
        from datetime import datetime
        token_hash = hash_token(access_token)
        create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=1),
            db=db,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Record successful login
        record_login_attempt(
            user.id,
            True,
            db,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

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
    except Exception:
        logger.exception("Login failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during login"
        )


# ========================
# 4. GET USER INFO
# ========================
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_current_user(
    token: str | None = Header(default=None, alias="X-User-Token"),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Get current user info from token.
    """
    bearer_token = extract_bearer_token(authorization)
    if authorization and not bearer_token:
        raise HTTPException(status_code=401, detail="Malformed Authorization header")
    if token and not settings.ALLOW_LEGACY_USER_TOKEN:
        raise HTTPException(status_code=401, detail="Legacy token header is disabled")
    token = bearer_token or token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )

    payload = get_token_payload(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    session = get_session_by_token_hash(hash_token(token), db)
    if not payload.get("external") and (not session or session.user_id != payload["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired",
        )

    user = get_user_by_id(payload["user_id"], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)
