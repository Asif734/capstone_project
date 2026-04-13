# schemas/authentication.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class SignUpRequest(BaseModel):
    """User signup request with validation"""
    reg_id: str = Field(..., min_length=3, max_length=20, description="Registration ID")
    email: EmailStr = Field(..., description="Valid email address")
    
    @field_validator("reg_id")
    @classmethod
    def validate_reg_id(cls, v):
        if not v.isalnum():
            raise ValueError("Registration ID must be alphanumeric")
        return v.upper()


class OTPVerifyRequest(BaseModel):
    """OTP verification and password setup"""
    reg_id: str = Field(..., min_length=3, max_length=20)
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Ensure password has uppercase, lowercase, and number"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    """User login credentials"""
    reg_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Successful login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Token expiry in seconds
    user_id: int
    reg_id: str
    message: str


class UserResponse(BaseModel):
    """User info response"""
    id: int
    reg_id: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: int
    reg_id: str
    exp: int  # Expiration timestamp
