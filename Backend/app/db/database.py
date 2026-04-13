from sqlalchemy.orm import Session
from app.db.sqldb import SessionLocal
from app.db.student_tables import AuthorizedUser, User, OTP, Session as DBSession, LoginHistory, StudentCourse, CGPARecord, FinancialRecord, AcademicRecord
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
STUDENT_FILE = BASE_DIR / "students.json"


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()


# ========== STUDENT VERIFICATION ==========
def find_student(reg_id: str, email: str, db: Session) -> AuthorizedUser | None:
    """Find student in authorized users list"""
    return db.query(AuthorizedUser).filter(
        AuthorizedUser.reg_id == reg_id,
        AuthorizedUser.email == email
    ).first()


def is_authorized_user(reg_id: str, email: str, db: Session) -> bool:
    """Return True when the student is authorized in the database"""
    return find_student(reg_id, email, db) is not None


def initialize_authorized_users(db: Session):
    """Load students from JSON into authorized_users table if empty"""
    if db.query(AuthorizedUser).count() == 0:
        try:
            with open(STUDENT_FILE, 'r') as f:
                students = json.load(f)
            for student in students:
                db_user = AuthorizedUser(
                    reg_id=student['reg_id'],
                    email=student['email']
                )
                db.add(db_user)
            db.commit()
        except Exception as e:
            print(f"Error loading students: {e}")
            db.rollback()


# ========== USER MANAGEMENT ==========
def user_exists(reg_id: str, db: Session) -> bool:
    """Check if user is registered"""
    return db.query(User).filter(User.reg_id == reg_id).first() is not None


def get_user_by_reg_id(reg_id: str, db: Session) -> User | None:
    """Get user by registration ID"""
    return db.query(User).filter(User.reg_id == reg_id).first()


def get_user_by_id(user_id: int, db: Session) -> User | None:
    """Get user by user ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(email: str, db: Session) -> User | None:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def save_user(reg_id: str, email: str, password_hash: str, db: Session) -> User:
    """Create a new verified user"""
    user = User(
        reg_id=reg_id,
        email=email,
        password_hash=password_hash,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_pass(reg_id: str, db: Session) -> str | None:
    """Get password hash for verification"""
    user = db.query(User).filter(User.reg_id == reg_id).first()
    return user.password_hash if user else None


def update_last_login(user_id: int, db: Session):
    """Update last login timestamp"""
    user = get_user_by_id(user_id, db)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()


def reset_login_attempts(user_id: int, db: Session):
    """Reset failed login attempts"""
    user = get_user_by_id(user_id, db)
    if user:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()


def increment_failed_login(user_id: int, db: Session, lock_minutes: int = 15):
    """Increment failed login attempts and lock account if needed"""
    user = get_user_by_id(user_id, db)
    if user:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)
        db.commit()


def is_account_locked(user_id: int, db: Session) -> bool:
    """Check if account is locked"""
    user = get_user_by_id(user_id, db)
    if not user:
        return False
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False


def deactivate_user(user_id: int, db: Session):
    """Deactivate user account"""
    user = get_user_by_id(user_id, db)
    if user:
        user.is_active = False
        db.commit()


# ========== OTP MANAGEMENT ==========
def save_otp(reg_id: str, email: str, otp: str, db: Session, expiry_minutes: int = 10):
    """Save OTP with expiration"""
    # Delete existing OTP
    db.query(OTP).filter(OTP.reg_id == reg_id).delete()
    
    # Create new OTP
    new_otp = OTP(
        reg_id=reg_id,
        email=email,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes)
    )
    db.add(new_otp)
    db.commit()


def get_otp(reg_id: str, db: Session) -> str | None:
    """Get valid OTP if not expired"""
    record = db.query(OTP).filter(OTP.reg_id == reg_id).first()
    if not record:
        return None
    if record.is_used:
        return None
    if record.expires_at < datetime.utcnow():
        return None
    return record.otp


def get_otp_email(reg_id: str, db: Session) -> str | None:
    """Get email from valid OTP record"""
    record = db.query(OTP).filter(OTP.reg_id == reg_id).first()
    if not record:
        return None
    if record.is_used:
        return None
    if record.expires_at < datetime.utcnow():
        return None
    return record.email


def increment_otp_attempts(reg_id: str, db: Session) -> int:
    """Increment OTP attempts and return current count"""
    record = db.query(OTP).filter(OTP.reg_id == reg_id).first()
    if record:
        record.attempts += 1
        db.commit()
        return record.attempts
    return 0


def mark_otp_as_used(reg_id: str, db: Session):
    """Mark OTP as used"""
    record = db.query(OTP).filter(OTP.reg_id == reg_id).first()
    if record:
        record.is_used = True
        db.commit()


def delete_otp(reg_id: str, db: Session):
    """Delete OTP record"""
    db.query(OTP).filter(OTP.reg_id == reg_id).delete()
    db.commit()


# ========== SESSION MANAGEMENT ==========
def create_session(user_id: int, token_hash: str, expires_at: datetime, db: Session, ip_address: str = None, user_agent: str = None) -> DBSession:
    """Create a new session"""
    session = DBSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_token_hash(token_hash: str, db: Session) -> DBSession | None:
    """Get active session by token hash"""
    return db.query(DBSession).filter(
        DBSession.token_hash == token_hash,
        DBSession.is_active == True,
        DBSession.expires_at > datetime.utcnow()
    ).first()


def invalidate_session(session_id: int, db: Session):
    """Invalidate a session"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        session.is_active = False
        db.commit()


def invalidate_user_sessions(user_id: int, db: Session):
    """Invalidate all sessions for a user (e.g., logout all devices)"""
    db.query(DBSession).filter(
        DBSession.user_id == user_id,
        DBSession.is_active == True
    ).update({"is_active": False})
    db.commit()


# ========== LOGIN HISTORY ==========
def record_login_attempt(user_id: int, success: bool, db: Session, ip_address: str = None, user_agent: str = None, reason: str = None):
    """Record a login attempt"""
    history = LoginHistory(
        user_id=user_id,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        reason=reason
    )
    db.add(history)
    db.commit()


def get_login_history(user_id: int, db: Session, limit: int = 10):
    """Get recent login attempts"""
    return db.query(LoginHistory).filter(
        LoginHistory.user_id == user_id
    ).order_by(LoginHistory.login_at.desc()).limit(limit).all()


# ========== STUDENT DATA POPULATION ==========
def populate_student_data_from_json(db: Session):
    """Populate student data from private.json into database tables"""
    import json
    from pathlib import Path
    
    private_file = BASE_DIR / "private.json"
    if not private_file.exists():
        print("private.json not found")
        return
    
    try:
        with open(private_file, 'r', encoding='utf-8') as f:
            student_data = json.load(f)
        
        for reg_id, data in student_data.items():
            # Check if user already exists
            existing_user = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == reg_id).first()
            if existing_user:
                # Update existing user
                existing_user.name = data.get('name')
                existing_user.year = data.get('year')
                existing_user.semester = data.get('semester')
                existing_user.department = data.get('department')
                existing_user.status = data.get('status', 'active')
            else:
                # Create new user
                user = AuthorizedUser(
                    reg_id=reg_id,  # Using reg_id as primary key
                    name=data.get('name'),
                    email=f"{reg_id.lower()}@university.edu",  # Default email since not in JSON
                    year=data.get('year'),
                    semester=data.get('semester'),
                    department=data.get('department'),
                    status=data.get('status', 'active')
                )
                db.add(user)
            
            # Add/Update courses
            if 'courses' in data and 'marks' in data:
                # Clear existing courses for this user
                db.query(StudentCourse).filter(StudentCourse.reg_id == reg_id).delete()
                
                for course_name in data['courses']:
                    marks = data['marks'].get(course_name)
                    course = StudentCourse(
                        reg_id=reg_id,
                        course_name=course_name,
                        marks=marks
                    )
                    db.add(course)
            
            # Add/Update CGPA records
            if 'cgpa' in data:
                # Clear existing CGPA records for this user
                db.query(CGPARecord).filter(CGPARecord.reg_id == reg_id).delete()
                
                for sem, cgpa in data['cgpa'].items():
                    cgpa_record = CGPARecord(
                        reg_id=reg_id,
                        semester=sem,
                        cgpa=cgpa
                    )
                    db.add(cgpa_record)
            
            # Add/Update financial record
            financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == reg_id).first()
            if financial:
                financial.pending_fees = data.get('pending_fees', 0)
            else:
                financial = FinancialRecord(
                    reg_id=reg_id,
                    pending_fees=data.get('pending_fees', 0)
                )
                db.add(financial)
            
            # Add/Update academic record (current semester record)
            if 'cgpa' in data:
                current_sem = f"sem{data.get('semester')}"
                current_cgpa = data['cgpa'].get(current_sem)
                
                if current_cgpa is not None:
                    # Calculate credits completed (12 credits per semester)
                    credits_completed = data.get('semester', 0) * 12
                    
                    # Clear existing academic record for this user
                    db.query(AcademicRecord).filter(AcademicRecord.reg_id == reg_id).delete()
                    
                    # Create new academic record
                    academic = AcademicRecord(
                        reg_id=reg_id,
                        semester=current_sem,
                        cgpa=current_cgpa,
                        credits_completed=credits_completed
                    )
                    db.add(academic)
        
        db.commit()
        print(f"Successfully populated data for {len(student_data)} students")
        
    except Exception as e:
        print(f"Error populating student data: {e}")
        db.rollback()


def get_student_data_by_reg_id(reg_id: str, db: Session) -> dict | None:
    """Get complete student data by registration ID"""
    user = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == reg_id).first()
    if not user:
        return None
    
    # Get courses
    courses = db.query(StudentCourse).filter(StudentCourse.reg_id == reg_id).all()
    courses_data = {}
    marks_data = {}
    for course in courses:
        courses_data[course.course_name] = course.marks or 0
        if course.marks:
            marks_data[course.course_name] = course.marks
    
    # Get CGPA records
    cgpa_records = db.query(CGPARecord).filter(CGPARecord.reg_id == reg_id).all()
    cgpa_data = {record.semester: record.cgpa for record in cgpa_records}
    
    # Get financial data
    financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == reg_id).first()
    pending_fees = financial.pending_fees if financial else 0
    
    return {
        "name": user.name,
        "year": user.year,
        "semester": user.semester,
        "department": user.department,
        "courses": list(courses_data.keys()),
        "marks": marks_data,
        "cgpa": cgpa_data,
        "pending_fees": pending_fees,
        "status": user.status
    }




# # database.py
# import json
# from pathlib import Path
# from typing import List, Dict, Any

# BASE_DIR = Path(__file__).resolve().parent

# STUDENT_FILE = BASE_DIR / "students.json"
# USERS_FILE = BASE_DIR / "users.json"
# OTP_FILE = BASE_DIR / "otp.json"


# # ----------------------------
# # Utility functions for JSON I/O
# # ----------------------------
# def read_json(file_path: Path) -> Any:
#     if not file_path.exists():
#         if file_path.suffix == ".json":
#             file_path.write_text("[]", encoding="utf-8")
#         return []
#     with open(file_path, "r", encoding="utf-8") as f:
#         return json.load(f)


# def write_json(file_path: Path, data: Any):
#     with open(file_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)


# # ----------------------------
# # Load students
# # ----------------------------
# def load_students() -> List[Dict[str, Any]]:
#     return read_json(STUDENT_FILE)


# def find_student(reg_id: str, email: str) -> Dict[str, str] | None:
#     students = load_students()
#     return next((s for s in students if s["reg_id"] == reg_id and s["email"] == email), None)


# # ----------------------------
# # Manage users (registered)
# # ----------------------------
# def load_users() -> Dict[str, Any]:
#     data = read_json(USERS_FILE)
#     return {item["reg_id"]: item for item in data}


# def save_user(reg_id: str, hashed_password: str):
#     users = read_json(USERS_FILE)
#     # Remove old entry if exists
#     users = [u for u in users if u["reg_id"] != reg_id]
#     users.append({"reg_id": reg_id, "password": hashed_password})
#     write_json(USERS_FILE, users)


# def user_exists(reg_id: str) -> bool:
#     users = read_json(USERS_FILE)
#     return any(u["reg_id"] == reg_id for u in users)


# def get_user_password(reg_id: str) -> str | None:
#     users = read_json(USERS_FILE)
#     user = next((u for u in users if u["reg_id"] == reg_id), None)
#     return user["password"] if user else None


# # ----------------------------
# # Manage OTP store (optional file-based)
# # ----------------------------
# def save_otp(reg_id: str, otp: str):
#     otps = read_json(OTP_FILE)
#     otps = [o for o in otps if o["reg_id"] != reg_id]
#     otps.append({"reg_id": reg_id, "otp": otp})
#     write_json(OTP_FILE, otps)


# def get_otp(reg_id: str) -> str | None:
#     otps = read_json(OTP_FILE)
#     record = next((o for o in otps if o["reg_id"] == reg_id), None)
#     return record["otp"] if record else None


# def delete_otp(reg_id: str):
#     otps = read_json(OTP_FILE)
#     otps = [o for o in otps if o["reg_id"] != reg_id]
#     write_json(OTP_FILE, otps)
