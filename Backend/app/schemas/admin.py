from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class AuthorizedStudentCreate(BaseModel):
    reg_id: str = Field(..., min_length=3, max_length=20)
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    year: Optional[int] = Field(default=None, ge=1, le=8)
    semester: Optional[int] = Field(default=None, ge=1, le=16)
    department: Optional[str] = Field(default=None, max_length=120)
    status: str = Field(default="active", max_length=40)

    @field_validator("reg_id")
    @classmethod
    def normalize_reg_id(cls, value):
        value = value.strip().upper()
        if not value.isalnum():
            raise ValueError("Registration ID must be alphanumeric")
        return value

    @field_validator("name", "department", "status")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class AuthorizedStudentResponse(BaseModel):
    id: int
    reg_id: str
    name: Optional[str] = None
    email: str
    year: Optional[int] = None
    semester: Optional[int] = None
    department: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class AuthorizedStudentUpdate(BaseModel):
    reg_id: Optional[str] = Field(default=None, min_length=3, max_length=20)
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    year: Optional[int] = Field(default=None, ge=1, le=8)
    semester: Optional[int] = Field(default=None, ge=1, le=16)
    department: Optional[str] = Field(default=None, max_length=120)
    status: Optional[str] = Field(default=None, max_length=40)

    @field_validator("reg_id")
    @classmethod
    def normalize_reg_id(cls, value):
        if value is None:
            return value
        value = value.strip().upper()
        if not value.isalnum():
            raise ValueError("Registration ID must be alphanumeric")
        return value

    @field_validator("name", "department", "status")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MentalHealthAlertResponse(BaseModel):
    id: int
    user_id: int
    reg_id: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    severity: str
    score: int
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    matched_phrases: Optional[str] = None
    question_sample: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class MentalHealthAlertUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=40)
    admin_notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        if value is None:
            return value
        normalized = value.strip().lower()
        allowed = {"new", "reviewed", "contacted", "closed"}
        if normalized not in allowed:
            raise ValueError("Status must be one of: new, reviewed, contacted, closed")
        return normalized


class StudentMentalHealthResponse(BaseModel):
    student: AuthorizedStudentResponse
    alerts: list[MentalHealthAlertResponse]


class AdminMentalHealthSummary(BaseModel):
    total_alerts: int
    new_alerts: int
    critical_alerts: int
    high_alerts: int
    moderate_alerts: int
    low_alerts: int
