# schemas/authentication.py
from pydantic import BaseModel, EmailStr

class SignUpRequest(BaseModel):
    reg_id: str
    email: EmailStr

class OTPVerifyRequest(BaseModel):
    reg_id: str
    otp: str
    password: str
    confirm_password: str

class LoginRequest(BaseModel):
    reg_id: str
    password: str
