# utils/authentication.py
import random, smtplib
from email.mime.text import MIMEText
import jwt
from app.core.config import settings  # or wherever you store SECRET_KEY
from fastapi import HTTPException

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(receiver_email: str, otp: str):
    # Simulated email sending
    print(f"[DEBUG] OTP sent to {receiver_email}: {otp}")
    
    # Example for real email (optional):
    """
    msg = MIMEText(f"Your OTP code is: {otp}")
    msg["Subject"] = "Student Auth Verification"
    msg["From"] = "your_email@gmail.com"
    msg["To"] = receiver_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("your_email@gmail.com", "your_app_password")
        server.send_message(msg)
    """




SECRET_KEY = settings.JWT_SECRET_KEY  # generate a random string in settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ------------------------
# Generate token (at login)
# ------------------------
def create_access_token(reg_id: str) -> str:
    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    payload = {"reg_id": reg_id}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# ------------------------
# Verify token
# ------------------------
def verify_user_token(token: str) -> bool:
    if not SECRET_KEY:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        reg_id = payload.get("reg_id")
        if not reg_id:
            return False
        # optionally: check if user exists in DB
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
