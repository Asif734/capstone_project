from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.db.sqldb import SessionLocal
from app.db.student_tables import AuthorizedUser, User, OTP, Session as DBSession, LoginHistory, MentalHealthAlert, StudentCourse, CGPARecord, FinancialRecord, AcademicRecord, AccessAuditLog
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


def ensure_schema_migrations(db: Session):
    """Apply lightweight SQLite-safe schema updates for existing local DBs."""
    inspector = inspect(db.bind)
    table_names = inspector.get_table_names()
    migrations = {
        "mental_health_alerts": {
            "predicted_class": "ALTER TABLE mental_health_alerts ADD COLUMN predicted_class VARCHAR",
            "confidence": "ALTER TABLE mental_health_alerts ADD COLUMN confidence FLOAT",
            "summary": "ALTER TABLE mental_health_alerts ADD COLUMN summary TEXT",
            "status": "ALTER TABLE mental_health_alerts ADD COLUMN status VARCHAR DEFAULT 'new'",
            "admin_notes": "ALTER TABLE mental_health_alerts ADD COLUMN admin_notes TEXT",
            "reviewed_at": "ALTER TABLE mental_health_alerts ADD COLUMN reviewed_at DATETIME",
            "closed_at": "ALTER TABLE mental_health_alerts ADD COLUMN closed_at DATETIME",
        },
        "users": {
            "consent_accepted_at": "ALTER TABLE users ADD COLUMN consent_accepted_at DATETIME",
            "consent_version": "ALTER TABLE users ADD COLUMN consent_version VARCHAR",
        },
        "otps": {
            "consent_accepted_at": "ALTER TABLE otps ADD COLUMN consent_accepted_at DATETIME",
            "consent_version": "ALTER TABLE otps ADD COLUMN consent_version VARCHAR",
        },
        "authorized_users": {
            "program": "ALTER TABLE authorized_users ADD COLUMN program VARCHAR",
            "faculty": "ALTER TABLE authorized_users ADD COLUMN faculty VARCHAR",
            "batch": "ALTER TABLE authorized_users ADD COLUMN batch VARCHAR",
            "advisor_name": "ALTER TABLE authorized_users ADD COLUMN advisor_name VARCHAR",
            "advisor_email": "ALTER TABLE authorized_users ADD COLUMN advisor_email VARCHAR",
            "enrollment_date": "ALTER TABLE authorized_users ADD COLUMN enrollment_date VARCHAR",
            "expected_graduation": "ALTER TABLE authorized_users ADD COLUMN expected_graduation VARCHAR",
        },
        "academic_records": {
            "total_cgpa": "ALTER TABLE academic_records ADD COLUMN total_cgpa FLOAT",
            "credits_required": "ALTER TABLE academic_records ADD COLUMN credits_required INTEGER DEFAULT 144",
            "attendance_percentage": "ALTER TABLE academic_records ADD COLUMN attendance_percentage FLOAT",
            "attendance_status": "ALTER TABLE academic_records ADD COLUMN attendance_status VARCHAR",
            "academic_standing": "ALTER TABLE academic_records ADD COLUMN academic_standing VARCHAR DEFAULT 'Good Standing'",
        },
        "financial_records": {
            "waiver_amount": "ALTER TABLE financial_records ADD COLUMN waiver_amount INTEGER DEFAULT 0",
            "payment_status": "ALTER TABLE financial_records ADD COLUMN payment_status VARCHAR DEFAULT 'paid'",
            "last_payment_date": "ALTER TABLE financial_records ADD COLUMN last_payment_date VARCHAR",
            "payment_deadline": "ALTER TABLE financial_records ADD COLUMN payment_deadline VARCHAR",
        },
        "student_courses": {
            "course_code": "ALTER TABLE student_courses ADD COLUMN course_code VARCHAR",
            "credits": "ALTER TABLE student_courses ADD COLUMN credits FLOAT DEFAULT 3.0",
            "semester": "ALTER TABLE student_courses ADD COLUMN semester VARCHAR",
            "grade": "ALTER TABLE student_courses ADD COLUMN grade VARCHAR",
            "status": "ALTER TABLE student_courses ADD COLUMN status VARCHAR DEFAULT 'enrolled'",
            "instructor": "ALTER TABLE student_courses ADD COLUMN instructor VARCHAR",
        },
        "cgpa_records": {
            "term_label": "ALTER TABLE cgpa_records ADD COLUMN term_label VARCHAR",
            "credits": "ALTER TABLE cgpa_records ADD COLUMN credits INTEGER DEFAULT 15",
        },
    }

    changed = False
    for table_name, table_migrations in migrations.items():
        if table_name not in table_names:
            continue
        existing_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for column_name, statement in table_migrations.items():
            if column_name not in existing_columns:
                db.execute(text(statement))
                changed = True

    if changed:
        if "mental_health_alerts" in table_names:
            db.execute(text("UPDATE mental_health_alerts SET status = 'new' WHERE status IS NULL"))
        db.commit()


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


def save_user(
    reg_id: str,
    email: str,
    password_hash: str,
    db: Session,
    consent_accepted_at: datetime,
    consent_version: str,
) -> User:
    """Create a new verified user"""
    user = User(
        reg_id=reg_id,
        email=email,
        password_hash=password_hash,
        is_verified=True,
        consent_accepted_at=consent_accepted_at,
        consent_version=consent_version,
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
def save_otp(
    reg_id: str,
    email: str,
    otp: str,
    db: Session,
    consent_version: str,
    expiry_minutes: int = 10,
):
    """Save OTP with expiration"""
    # Delete existing OTP
    db.query(OTP).filter(OTP.reg_id == reg_id).delete()
    
    # Create new OTP
    new_otp = OTP(
        reg_id=reg_id,
        email=email,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
        consent_accepted_at=datetime.utcnow(),
        consent_version=consent_version,
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


def get_otp_consent(reg_id: str, db: Session) -> tuple[datetime, str] | None:
    """Return consent evidence from a valid, pending OTP."""
    record = db.query(OTP).filter(OTP.reg_id == reg_id).first()
    if (
        not record
        or record.is_used
        or record.expires_at < datetime.utcnow()
        or not record.consent_accepted_at
        or not record.consent_version
    ):
        return None
    return record.consent_accepted_at, record.consent_version


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


def save_mental_health_alert(
    user_id: int,
    reg_id: str | None,
    severity: str,
    score: int,
    matched_phrases: str,
    question_sample: str,
    db: Session,
    predicted_class: str | None = None,
    confidence: float | None = None,
    summary: str | None = None,
) -> MentalHealthAlert:
    """Persist a mental-health risk alert."""
    alert = MentalHealthAlert(
        user_id=user_id,
        reg_id=reg_id,
        severity=severity,
        score=score,
        predicted_class=predicted_class,
        confidence=confidence,
        summary=summary,
        matched_phrases=matched_phrases,
        question_sample=question_sample,
        status="new",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    try:
        from app.services.audit_service import log_data_access_sync
        log_data_access_sync(
            agent_node="mental_health_agent",
            action_type="COUNSELOR_ALERT_CREATED",
            auth_status="AUTHORIZED",
            actor_student_id=str(reg_id) if reg_id else None,
            target_student_id=str(reg_id) if reg_id else None,
            db=db,
        )
    except Exception:
        pass

    return alert


def get_recent_mental_health_alerts(user_id: int, db: Session, hours: int = 24):
    """Return alerts created within the last `hours` hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    return db.query(MentalHealthAlert).filter(
        MentalHealthAlert.user_id == user_id,
        MentalHealthAlert.created_at >= cutoff,
    ).order_by(MentalHealthAlert.created_at.desc()).all()


def _marks_to_letter_grade(marks: float | None) -> str | None:
    """Convert numeric marks (0-100) to BUP UGC uniform letter grade."""
    if marks is None:
        return None
    if marks >= 80:
        return "A+"
    if marks >= 75:
        return "A"
    if marks >= 70:
        return "A-"
    if marks >= 65:
        return "B+"
    if marks >= 60:
        return "B"
    if marks >= 55:
        return "B-"
    if marks >= 50:
        return "C+"
    if marks >= 45:
        return "C"
    if marks >= 40:
        return "D"
    return "F"


def _infer_faculty_and_program(department: str | None) -> tuple[str | None, str | None, int]:
    """Infer faculty, program title, and required credits from department name."""
    dept = (department or "").lower()
    if any(k in dept for k in ("computer", "ai", "cse", "cyber", "network", "ice", "ict", "software")):
        return "Faculty of Science & Technology (FST)", f"B.Sc. in {department}", 144
    if any(k in dept for k in ("environmental",)):
        return "Faculty of Science & Technology (FST)", f"B.Sc. (Hons) in {department}", 132
    if any(k in dept for k in ("bba", "business", "finance", "marketing", "accounting", "management")):
        return "Faculty of Business Studies (FBS)", f"BBA in {department}", 126
    if any(k in dept for k in ("law", "llb")):
        return "Faculty of Security & Strategic Studies (FSSS)", "Bachelor of Laws (LLB Hons)", 134
    if any(k in dept for k in ("international", "peace", "journalism", "mass comm")):
        return "Faculty of Security & Strategic Studies (FSSS)", f"BSS (Hons) in {department}", 126
    if any(k in dept for k in ("economics", "english", "sociology", "development", "public admin", "disaster")):
        return "Faculty of Arts & Social Sciences (FASS)", f"BSS (Hons) in {department}", 126
    if department:
        return "Faculty of Science & Technology (FST)", f"B.Sc. in {department}", 144
    return None, None, 144


def _compute_total_cgpa(cgpa_records: list[CGPARecord]) -> float | None:
    """Compute cumulative CGPA across all recorded semesters (credit-weighted if available)."""
    if not cgpa_records:
        return None
    total_weight = sum((rec.credits or 15) for rec in cgpa_records)
    if total_weight <= 0:
        return round(sum(rec.cgpa for rec in cgpa_records) / len(cgpa_records), 2)
    weighted_sum = sum(rec.cgpa * (rec.credits or 15) for rec in cgpa_records)
    return round(weighted_sum / total_weight, 2)


# ========== STUDENT DATA POPULATION ==========
def populate_student_data_from_json(db: Session):
    """Populate student data from private.json into database tables"""
    private_file = BASE_DIR / "private.json"
    if not private_file.exists():
        print("private.json not found")
        return

    try:
        with open(private_file, 'r', encoding='utf-8') as f:
            student_data = json.load(f)

        for reg_id, data in student_data.items():
            dept = data.get('department')
            faculty, program, default_req_credits = _infer_faculty_and_program(dept)
            year = data.get('year')
            semester = data.get('semester')
            batch = data.get('batch') or (f"Batch {reg_id[:4]}" if reg_id[:4].isdigit() else "Batch 2023")

            existing_user = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == reg_id).first()
            if existing_user:
                existing_user.name = data.get('name')
                existing_user.year = year
                existing_user.semester = semester
                existing_user.department = dept
                existing_user.program = existing_user.program or data.get('program') or program
                existing_user.faculty = existing_user.faculty or data.get('faculty') or faculty
                existing_user.batch = existing_user.batch or batch
                existing_user.advisor_name = existing_user.advisor_name or data.get('advisor_name') or "Dr. Tariqul Islam"
                existing_user.advisor_email = existing_user.advisor_email or data.get('advisor_email') or "advisor@bup.edu.bd"
                existing_user.enrollment_date = existing_user.enrollment_date or data.get('enrollment_date') or "2023-01-15"
                existing_user.expected_graduation = existing_user.expected_graduation or data.get('expected_graduation') or "2026-12"
                existing_user.status = data.get('status', 'active')
            else:
                user = AuthorizedUser(
                    reg_id=reg_id,
                    name=data.get('name'),
                    email=f"{reg_id.lower()}@university.edu",
                    program=data.get('program') or program,
                    faculty=data.get('faculty') or faculty,
                    department=dept,
                    batch=batch,
                    year=year,
                    semester=semester,
                    advisor_name=data.get('advisor_name') or "Dr. Tariqul Islam",
                    advisor_email=data.get('advisor_email') or "advisor@bup.edu.bd",
                    enrollment_date=data.get('enrollment_date') or "2023-01-15",
                    expected_graduation=data.get('expected_graduation') or "2026-12",
                    status=data.get('status', 'active'),
                )
                db.add(user)

            # Add/Update courses
            if 'courses' in data and 'marks' in data:
                db.query(StudentCourse).filter(StudentCourse.reg_id == reg_id).delete()
                sem_label = f"sem{semester}" if semester else "current"
                for idx, course_name in enumerate(data['courses'], start=1):
                    marks = data['marks'].get(course_name)
                    course_code = f"CSE{semester or 1}10{idx}" if "computer" in (dept or "").lower() or "ai" in (dept or "").lower() else f"BUP{semester or 1}10{idx}"
                    course = StudentCourse(
                        reg_id=reg_id,
                        course_code=course_code,
                        course_name=course_name,
                        credits=3.0,
                        semester=sem_label,
                        marks=marks,
                        grade=_marks_to_letter_grade(marks),
                        status="enrolled",
                    )
                    db.add(course)

            # Add/Update CGPA records
            if 'cgpa' in data:
                db.query(CGPARecord).filter(CGPARecord.reg_id == reg_id).delete()
                for sem, cgpa in data['cgpa'].items():
                    cgpa_record = CGPARecord(
                        reg_id=reg_id,
                        semester=sem,
                        cgpa=cgpa,
                        credits=15,
                    )
                    db.add(cgpa_record)

            # Add/Update financial record (keep due_amount and pending_fees synchronized)
            due_val = int(data.get('due_amount', data.get('pending_fees', 0)) or 0)
            tuition_val = int(data.get('tuition_fee') or 20000)
            waiver_val = int(data.get('waiver_amount') or 0)
            paid_val = int(data.get('paid_amount') if data.get('paid_amount') is not None else max(0, tuition_val - waiver_val - due_val))
            payment_status = "paid" if due_val == 0 else ("partial" if paid_val > 0 else "due")

            financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == reg_id).first()
            if financial:
                financial.tuition_fee = financial.tuition_fee or tuition_val
                financial.waiver_amount = financial.waiver_amount if financial.waiver_amount is not None else waiver_val
                financial.paid_amount = financial.paid_amount if financial.paid_amount is not None else paid_val
                financial.due_amount = due_val if financial.due_amount is None else financial.due_amount
                financial.pending_fees = due_val if financial.pending_fees is None else financial.pending_fees
                financial.payment_status = "paid" if (financial.due_amount or financial.pending_fees or 0) == 0 else ("partial" if (financial.paid_amount or 0) > 0 else "due")
            else:
                financial = FinancialRecord(
                    reg_id=reg_id,
                    tuition_fee=tuition_val,
                    waiver_amount=waiver_val,
                    paid_amount=paid_val,
                    due_amount=due_val,
                    pending_fees=due_val,
                    payment_status=payment_status,
                    last_payment_date=data.get('last_payment_date') or "2026-10-15",
                    payment_deadline=data.get('payment_deadline') or ("2026-12-15" if due_val > 0 else None),
                )
                db.add(financial)

            # Add/Update academic summary record
            if 'cgpa' in data and data['cgpa']:
                current_sem = f"sem{semester}" if semester else list(data['cgpa'].keys())[-1]
                current_cgpa = data['cgpa'].get(current_sem) or list(data['cgpa'].values())[-1]
                cgpa_vals = list(data['cgpa'].values())
                total_cgpa = round(sum(cgpa_vals) / len(cgpa_vals), 2)
                credits_completed = (semester or len(cgpa_vals)) * 15
                standing = "Dean's List" if total_cgpa >= 3.80 else ("Good Standing" if total_cgpa >= 2.50 else "Academic Probation")

                db.query(AcademicRecord).filter(AcademicRecord.reg_id == reg_id).delete()
                academic = AcademicRecord(
                    reg_id=reg_id,
                    semester=current_sem,
                    cgpa=current_cgpa,
                    total_cgpa=total_cgpa,
                    credits_completed=credits_completed,
                    credits_required=default_req_credits,
                    attendance_percentage=88.5,
                    attendance_status="Collegiate",
                    academic_standing=standing,
                )
                db.add(academic)

        db.commit()
        print(f"Successfully populated data for {len(student_data)} students")

    except Exception as e:
        print(f"Error populating student data: {e}")
        db.rollback()


def get_student_data_by_reg_id(reg_id: str, db: Session) -> dict | None:
    """Get complete, user-friendly student academic journey data by registration ID."""
    user = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == reg_id).first()
    if not user:
        return None

    courses = db.query(StudentCourse).filter(StudentCourse.reg_id == reg_id).all()
    marks_data = {}
    current_courses = []
    for course in courses:
        if course.marks is not None:
            marks_data[course.course_name] = course.marks
        current_courses.append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "credits": course.credits if course.credits is not None else 3.0,
            "semester": course.semester or (f"sem{user.semester}" if user.semester else None),
            "marks": course.marks,
            "grade": course.grade or _marks_to_letter_grade(course.marks),
            "status": course.status or "enrolled",
            "instructor": course.instructor,
        })

    cgpa_records = (
        db.query(CGPARecord)
        .filter(CGPARecord.reg_id == reg_id)
        .order_by(CGPARecord.semester.asc())
        .all()
    )
    cgpa_data = {record.semester: record.cgpa for record in cgpa_records}
    semester_details = [
        {
            "semester": record.semester,
            "term_label": record.term_label,
            "sgpa": record.cgpa,
            "credits": record.credits,
        }
        for record in cgpa_records
    ]

    academic = db.query(AcademicRecord).filter(AcademicRecord.reg_id == reg_id).first()
    computed_total_cgpa = _compute_total_cgpa(cgpa_records)
    total_cgpa = (
        academic.total_cgpa
        if (academic and academic.total_cgpa is not None)
        else computed_total_cgpa
    )

    financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == reg_id).first()
    if financial:
        # Use whichever non-zero due field is populated so dues are never hidden
        if financial.due_amount is not None and financial.due_amount > 0:
            effective_due = financial.due_amount
        elif financial.pending_fees is not None and financial.pending_fees > 0:
            effective_due = financial.pending_fees
        else:
            effective_due = 0

        tuition_fee = financial.tuition_fee or 0
        waiver_amount = financial.waiver_amount or 0
        paid_amount = financial.paid_amount or 0
        payment_status = (
            "paid"
            if effective_due == 0
            else ("partial" if paid_amount > 0 else "due")
        )
        financial_summary = {
            "tuition_fee": tuition_fee,
            "waiver_amount": waiver_amount,
            "paid_amount": paid_amount,
            "due_amount": effective_due,
            "pending_fees": effective_due,
            "payment_status": payment_status,
            "last_payment_date": financial.last_payment_date,
            "payment_deadline": financial.payment_deadline,
        }
    else:
        effective_due = 0
        financial_summary = {
            "tuition_fee": 0,
            "waiver_amount": 0,
            "paid_amount": 0,
            "due_amount": 0,
            "pending_fees": 0,
            "payment_status": "paid",
            "last_payment_date": None,
            "payment_deadline": None,
        }

    inferred_faculty, inferred_program, inferred_req_credits = _infer_faculty_and_program(user.department)

    return {
        "profile": {
            "reg_id": user.reg_id,
            "name": user.name,
            "email": user.email,
            "program": user.program or inferred_program,
            "faculty": user.faculty or inferred_faculty,
            "department": user.department,
            "batch": user.batch,
            "current_year": user.year,
            "current_semester": user.semester,
            "status": user.status,
            "advisor": {
                "name": user.advisor_name,
                "email": user.advisor_email,
            } if (user.advisor_name or user.advisor_email) else None,
            "enrollment_date": user.enrollment_date,
            "expected_graduation": user.expected_graduation,
        },
        "academic_summary": {
            "total_cgpa": total_cgpa,
            "current_semester": academic.semester if academic else (f"sem{user.semester}" if user.semester else None),
            "current_semester_gpa": academic.cgpa if academic else (cgpa_data.get(f"sem{user.semester}") if user.semester else None),
            "credits_completed": academic.credits_completed if academic else None,
            "credits_required": (academic.credits_required if academic and academic.credits_required else inferred_req_credits),
            "attendance_percentage": academic.attendance_percentage if academic else None,
            "attendance_status": academic.attendance_status if academic else None,
            "academic_standing": academic.academic_standing if academic else None,
        },
        "semester_cgpa": cgpa_data,
        "semester_details": semester_details,
        "current_courses": current_courses,
        "financial": financial_summary,
        # Backwards-compatible top-level keys
        "name": user.name,
        "email": user.email,
        "year": user.year,
        "semester": user.semester,
        "department": user.department,
        "courses": [c["course_name"] for c in current_courses],
        "marks": marks_data,
        "cgpa": cgpa_data,
        "total_cgpa": total_cgpa,
        "pending_fees": effective_due,
        "due_amount": effective_due,
        "status": user.status,
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
