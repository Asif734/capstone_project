from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.db.sqldb import Base


class AuthorizedUser(Base):
    __tablename__ = "authorized_users"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    year = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    department = Column(String, nullable=True)
    status = Column(String, default="active")  # active, graduated, etc.

    academic = relationship(
        "AcademicRecord",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    financial = relationship(
        "FinancialRecord",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    courses = relationship(
        "StudentCourse",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    cgpa_records = relationship(
        "CGPARecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    reg_id = Column(
        String,
        ForeignKey("authorized_users.reg_id", ondelete="CASCADE"),
        primary_key=True
    )

    semester = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    credits_completed = Column(Integer)

    user = relationship("AuthorizedUser", back_populates="academic")


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    reg_id = Column(
        String,
        ForeignKey("authorized_users.reg_id", ondelete="CASCADE"),
        primary_key=True
    )

    tuition_fee = Column(Integer)
    paid_amount = Column(Integer)
    due_amount = Column(Integer)
    pending_fees = Column(Integer, default=0)

    user = relationship("AuthorizedUser", back_populates="financial")


class StudentCourse(Base):
    __tablename__ = "student_courses"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, ForeignKey("authorized_users.reg_id", ondelete="CASCADE"), nullable=False, index=True)
    course_name = Column(String, nullable=False)
    marks = Column(Float, nullable=True)

    user = relationship("AuthorizedUser", back_populates="courses")


class CGPARecord(Base):
    __tablename__ = "cgpa_records"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, ForeignKey("authorized_users.reg_id", ondelete="CASCADE"), nullable=False, index=True)
    semester = Column(String, nullable=False)  # e.g., "sem1", "sem2"
    cgpa = Column(Float, nullable=False)

    user = relationship("AuthorizedUser", back_populates="cgpa_records")


class User(Base):
    """Production-ready User model with enhanced security"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    consent_accepted_at = Column(DateTime, nullable=True)
    consent_version = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Security tracking
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    login_history = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")


class OTP(Base):
    """OTP model with expiration tracking"""
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    otp = Column(String, nullable=False)
    
    # Track attempts and expiration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    is_used = Column(Boolean, default=False)
    consent_accepted_at = Column(DateTime, nullable=True)
    consent_version = Column(String, nullable=True)


class Session(Base):
    """Store active sessions for token management"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="sessions")


class LoginHistory(Base):
    """Track login attempts for audit and security"""
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    login_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    reason = Column(String, nullable=True)  # e.g., "password_mismatch", "user_not_found"
    
    user = relationship("User", back_populates="login_history")


class MentalHealthAlert(Base):
    """Store alerts raised by continuous mental-health risk detection."""
    __tablename__ = "mental_health_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reg_id = Column(String, nullable=True, index=True)
    severity = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    predicted_class = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    matched_phrases = Column(String, nullable=True)
    question_sample = Column(Text, nullable=True)
    status = Column(String, default="new", nullable=False, index=True)
    admin_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notified = Column(Boolean, default=True)

    user = relationship("User")


class ChatInteraction(Base):
    """Durable per-conversation memory for deployed environments."""
    __tablename__ = "chat_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_key = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)


class AccessAuditLog(Base):
    """
    FERPA-compliant immutable access audit log.
    Records private student record lookups and unauthorized access attempts.
    Zero raw PII (names, full messages, marks, CGPA) is recorded.
    """
    __tablename__ = "access_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    actor_student_id = Column(String(64), nullable=True, index=True)
    target_student_id = Column(String(64), nullable=True, index=True)
    agent_node = Column(String(64), nullable=False, index=True)
    action_type = Column(String(64), nullable=False, index=True)
    auth_status = Column(String(32), nullable=False, index=True)
    token_jti = Column(String(128), nullable=True, index=True)
    client_ip = Column(String(64), nullable=True)

