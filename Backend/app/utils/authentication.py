# utils/authentication.py
import random
import string
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings

# ========== PASSWORD HASHING ==========
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase rounds for stronger hashing
)


import hashlib

def hash_password(password: str) -> str:
    # Normalize password length safely
    prehashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    # Then bcrypt
    return pwd_context.hash(prehashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(prehashed, hashed_password)

# ========== OTP GENERATION ==========
def generate_otp(length: int = 6) -> str:
    """Generate a secure 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(receiver_email: str, otp: str):
    """Send OTP via email (currently simulated)"""
    print(f"[DEBUG] OTP sent to {receiver_email}: {otp}")
    
    # Production: Connect to email service (SendGrid, AWS SES, etc.)
    # Example:
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    message = Mail(
        from_email='noreply@bup.edu.bd',
        to_emails=receiver_email,
        subject='BUP Student Portal - Email Verification',
        html_content=f'Your OTP is: {otp}'
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"Email failed: {e}")
    """


# ========== JWT TOKEN MANAGEMENT ==========
SECRET_KEY = settings.JWT_SECRET_KEY or "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_token(token: str) -> str:
    """Create hash of token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: int, reg_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with user info"""
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "user_id": user_id,
        "reg_id": reg_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: int, reg_id: str) -> str:
    """Create refresh token for getting new access tokens"""
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "user_id": user_id,
        "reg_id": reg_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any] | None:
    """Verify JWT token and return payload"""
    if not SECRET_KEY:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        reg_id = payload.get("reg_id")
        token_type = payload.get("type")
        
        if not user_id or not reg_id:
            return None
        
        return {
            "user_id": user_id,
            "reg_id": reg_id,
            "type": token_type
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_user_token(token: str) -> bool:
    """Quick check: is token valid?"""
    return verify_token(token) is not None


def get_token_payload(token: str) -> Dict[str, Any] | None:
    """Get complete token payload"""
    return verify_token(token)


# ========== ACCOUNT SECURITY ==========
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain digit"
    
    # Optional: Check for special characters
    if not any(c in string.punctuation for c in password):
        return False, "Password must contain special character (!@#$%^&*)"
    
    return True, "Password is strong"


# ========== SECURITY UTILITIES ==========
def get_token_expiry_from_payload(payload: Dict) -> Optional[datetime]:
    """Extract expiry time from JWT payload"""
    exp = payload.get("exp")
    if exp:
        return datetime.fromtimestamp(exp)
    return None


def generate_secure_token() -> str:
    """Generate a random secure token"""
    return secrets.token_urlsafe(32)


import secrets

