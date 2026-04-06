import os
from fastapi import APIRouter, HTTPException, Depends
from passlib.context import CryptContext
from app.schemas.authentication import SignUpRequest, OTPVerifyRequest, LoginRequest
from app.utils.authentication import generate_otp, send_otp_email, create_access_token
from sqlalchemy.orm import Session
from app.db.database import (
    get_db,
    find_student,
    save_otp,
    get_otp,
    delete_otp,
    save_user,
    get_user_pass,
    user_exists,
)

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, stored_hash: str) -> bool:
    return pwd_context.verify(password, stored_hash)

# ------------------------
# 1. Sign Up: Send OTP
# ------------------------
@router.post("/signup")
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    # Check if student exists in students.json
    student = find_student(data.reg_id, data.email, db)
    if not student:
        raise HTTPException(status_code=400, detail="Invalid registration ID or email")

    # Check if already registered
    if user_exists(data.reg_id, db):
        raise HTTPException(status_code=400, detail="User already registered")

    # Generate OTP
    otp = generate_otp()
    save_otp(data.reg_id, otp, db)
    send_otp_email(data.email, otp)

    return {"message": f"OTP sent to {data.email}"}


# ------------------------
# 2. Verify OTP + Set Password
# ------------------------
@router.post("/verify-otp")
def verify_otp(data: OTPVerifyRequest, db: Session = Depends(get_db)):
    otp = get_otp(data.reg_id, db)

    if otp is None:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")

    if otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Save user
    hashed_pw = hash_password(data.password)
    save_user(data.reg_id, hashed_pw, db)
    delete_otp(data.reg_id, db)

    return {"message": "Registration successful! You can now log in."}


# ------------------------
# 3. Log In
# ------------------------
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    if not user_exists(data.reg_id, db):
        raise HTTPException(status_code=400, detail="User not found")

    stored_hash = get_user_pass(data.reg_id, db)
    if not stored_hash:
        raise HTTPException(status_code=400, detail="Password not set")

    # Verify password
    if not verify_password(data.password, stored_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")


    token = create_access_token(data.reg_id)

    return {"message": f"Login successful for {data.reg_id}","access_token": token}


