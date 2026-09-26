# utils/authentication.py
import hashlib
import hmac
import logging
import secrets
import smtplib
import string
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# ========== PASSWORD HASHING ==========
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase rounds for stronger hashing
)

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
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hash a short-lived OTP before storing it."""
    if not SECRET_KEY:
        raise RuntimeError("JWT secret not configured")
    return hmac.new(
        SECRET_KEY.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp_value(candidate: str, stored_value: str) -> bool:
    """Verify a hashed OTP, while allowing existing plaintext records."""
    expected = hash_otp(candidate)
    return hmac.compare_digest(expected, stored_value) or hmac.compare_digest(candidate, stored_value)


def send_otp_email(receiver_email: str, otp: str):
    """Send OTP via configured SMTP, or log it during local development."""
    if settings.REQUIRE_EMAIL_DELIVERY:
        _send_email(
            receiver_email,
            "BUP Student Portal - Email Verification",
            f"Your one-time verification code is {otp}. It expires in 10 minutes.",
        )
        return

    if settings.APP_ENV == "development":
        logger.warning("Development OTP for %s: %s", receiver_email, otp)
    
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


def send_admin_notification(email: str, subject: str, message: str):
    """Notify the admin about risk detection events."""
    if not email:
        logger.error("No admin email configured; notification skipped")
        return

    if settings.REQUIRE_EMAIL_DELIVERY:
        _send_email(email, subject, message)
        return

    logger.warning("Admin alert for %s (%s): %s", email, subject, message)

    # Example production implementation:
    # from sendgrid import SendGridAPIClient
    # from sendgrid.helpers.mail import Mail
    # mail = Mail(
    #     from_email='noreply@bup.edu.bd',
    #     to_emails=email,
    #     subject=subject,
    #     html_content=message,
    # )
    # try:
    #     sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    #     sg.send(mail)
    # except Exception as e:
    #     print(f"Admin notification failed: {e}")


def _send_email(receiver_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_HOST and SMTP_FROM_EMAIL must be configured")

    email = EmailMessage()
    email["From"] = settings.SMTP_FROM_EMAIL
    email["To"] = receiver_email
    email["Subject"] = subject
    email.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as client:
        if settings.SMTP_USE_TLS:
            client.starttls()
        if settings.SMTP_USERNAME:
            client.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        client.send_message(email)


# ========== JWT TOKEN MANAGEMENT ==========
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_token(token: str) -> str:
    """Create hash of token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract a well-formed Bearer token from an Authorization header."""
    if not authorization:
        return None
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def has_scope(payload: Dict[str, Any], required_scope: str) -> bool:
    return required_scope in str(payload.get("scope", "")).split()


def create_access_token(
    user_id: int,
    reg_id: str,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[list[str]] = None,
) -> str:
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
        "type": "access",
        "scope": " ".join(scopes or ["student.profile.read"]),
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
        if settings.APP_ENV == "production":
            jwks_client = jwt.PyJWKClient(settings.OAUTH_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
                audience=settings.OAUTH_AUDIENCE,
                issuer=settings.OAUTH_ISSUER,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
            user_id = payload.get(settings.OAUTH_USER_ID_CLAIM)
            reg_id = payload.get(settings.OAUTH_REG_ID_CLAIM)
            external = True
        else:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            reg_id = payload.get("reg_id")
            external = False
        token_type = payload.get("type")
        
        if not user_id or not reg_id or (not external and token_type != "access"):
            return None
        
        return {
            "user_id": user_id,
            "reg_id": reg_id,
            "type": token_type,
            "scope": payload.get("scope", ""),
            "external": external,
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
