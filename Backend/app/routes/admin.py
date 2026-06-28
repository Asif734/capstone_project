import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.student_tables import (
    AcademicRecord,
    AuthorizedUser,
    CGPARecord,
    FinancialRecord,
    MentalHealthAlert,
    StudentCourse,
)
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMentalHealthSummary,
    AuthorizedStudentCreate,
    AuthorizedStudentResponse,
    AuthorizedStudentUpdate,
    MentalHealthAlertResponse,
    MentalHealthAlertUpdate,
    StudentMentalHealthResponse,
    StudentRecordResponse,
    StudentRecordUpdate,
)


router = APIRouter(prefix="/admin", tags=["Admin"])

SEVERITY_PRIORITY = {
    "critical": 0,
    "high": 1,
    "moderate": 2,
    "low": 3,
}

STATUS_PRIORITY = {
    "new": 0,
    "reviewed": 1,
    "contacted": 2,
    "closed": 3,
}


def require_admin(
    admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    expected = settings.ADMIN_DASHBOARD_TOKEN
    if not admin_token or not expected or not hmac.compare_digest(admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )


@router.post("/login", response_model=AdminLoginResponse, status_code=status.HTTP_200_OK)
def admin_login(data: AdminLoginRequest):
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin login is not configured properly",
        )

    email_valid = hmac.compare_digest(
        data.email.strip().lower(),
        settings.ADMIN_EMAIL.strip().lower(),
    )
    password_valid = hmac.compare_digest(data.password, settings.ADMIN_PASSWORD)

    if not email_valid or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
        )

    return AdminLoginResponse(
        access_token=settings.ADMIN_DASHBOARD_TOKEN,
        token_type="bearer",
    )


def sort_alerts(alerts: list[MentalHealthAlert]) -> list[MentalHealthAlert]:
    return sorted(
        alerts,
        key=lambda alert: (
            SEVERITY_PRIORITY.get((alert.severity or "").lower(), 99),
            STATUS_PRIORITY.get((alert.status or "new").lower(), 99),
            -(alert.created_at.timestamp() if alert.created_at else 0),
        ),
    )


def serialize_alert(
    alert: MentalHealthAlert,
    student: AuthorizedUser | None = None,
) -> MentalHealthAlertResponse:
    return MentalHealthAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        reg_id=alert.reg_id,
        student_name=student.name if student else None,
        student_email=student.email if student else None,
        severity=alert.severity,
        score=alert.score,
        predicted_class=alert.predicted_class,
        confidence=alert.confidence,
        summary=alert.summary,
        matched_phrases=alert.matched_phrases,
        question_sample=alert.question_sample,
        status=alert.status or "new",
        admin_notes=alert.admin_notes,
        created_at=alert.created_at,
        reviewed_at=alert.reviewed_at,
        closed_at=alert.closed_at,
    )


def student_lookup_for_alerts(db: Session, alerts: list[MentalHealthAlert]) -> dict[str, AuthorizedUser]:
    reg_ids = {alert.reg_id for alert in alerts if alert.reg_id}
    if not reg_ids:
        return {}

    students = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id.in_(reg_ids)).all()
    return {student.reg_id: student for student in students}


def serialize_student_record(student: AuthorizedUser, db: Session) -> StudentRecordResponse:
    academic = db.query(AcademicRecord).filter(AcademicRecord.reg_id == student.reg_id).first()
    financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == student.reg_id).first()
    cgpa_records = (
        db.query(CGPARecord)
        .filter(CGPARecord.reg_id == student.reg_id)
        .order_by(CGPARecord.semester.asc())
        .all()
    )
    courses = (
        db.query(StudentCourse)
        .filter(StudentCourse.reg_id == student.reg_id)
        .order_by(StudentCourse.course_name.asc())
        .all()
    )

    return StudentRecordResponse(
        student=student,
        academic={
            "semester": academic.semester,
            "cgpa": academic.cgpa,
            "credits_completed": academic.credits_completed,
        } if academic else None,
        financial={
            "tuition_fee": financial.tuition_fee if financial else 0,
            "paid_amount": financial.paid_amount if financial else 0,
            "due_amount": financial.due_amount if financial else 0,
            "pending_fees": financial.pending_fees if financial else 0,
        },
        cgpa_records=[
            {"semester": record.semester, "cgpa": record.cgpa}
            for record in cgpa_records
        ],
        courses=[
            {"course_name": course.course_name, "marks": course.marks}
            for course in courses
        ],
    )


@router.get("/authorized-students", response_model=list[AuthorizedStudentResponse])
def list_authorized_students(
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(AuthorizedUser).order_by(AuthorizedUser.reg_id.asc()).all()


@router.post(
    "/authorized-students",
    response_model=AuthorizedStudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_authorized_student(
    data: AuthorizedStudentCreate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing_reg = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == data.reg_id).first()
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this registration ID already exists",
        )

    existing_email = db.query(AuthorizedUser).filter(AuthorizedUser.email == data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this email already exists",
        )

    student = AuthorizedUser(
        reg_id=data.reg_id,
        name=data.name,
        email=str(data.email),
        year=data.year,
        semester=data.semester,
        department=data.department,
        status=data.status or "active",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/authorized-students/{student_id}", response_model=AuthorizedStudentResponse)
def update_authorized_student(
    student_id: int,
    data: AuthorizedStudentUpdate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = db.query(AuthorizedUser).filter(AuthorizedUser.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if data.reg_id and data.reg_id != student.reg_id:
        existing_reg = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == data.reg_id).first()
        if existing_reg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this registration ID already exists",
            )
        student.reg_id = data.reg_id

    if data.email and data.email != student.email:
        existing_email = db.query(AuthorizedUser).filter(AuthorizedUser.email == data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this email already exists",
            )
        student.email = str(data.email)

    if data.name is not None:
        student.name = data.name
    if data.department is not None:
        student.department = data.department
    if data.year is not None:
        student.year = data.year
    if data.semester is not None:
        student.semester = data.semester
    if data.status is not None:
        student.status = data.status

    db.commit()
    db.refresh(student)
    return student


@router.delete("/authorized-students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_authorized_student(
    student_id: int,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    student = db.query(AuthorizedUser).filter(AuthorizedUser.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(student)
    db.commit()
    return None


@router.get("/students/{reg_id}/records", response_model=StudentRecordResponse)
def get_student_records(
    reg_id: str,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_reg_id = reg_id.strip().upper()
    student = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == normalized_reg_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return serialize_student_record(student, db)


@router.patch("/students/{reg_id}/records", response_model=StudentRecordResponse)
def update_student_records(
    reg_id: str,
    data: StudentRecordUpdate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_reg_id = reg_id.strip().upper()
    student = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == normalized_reg_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if data.academic is not None:
        academic = db.query(AcademicRecord).filter(AcademicRecord.reg_id == normalized_reg_id).first()
        if not academic:
            academic = AcademicRecord(
                reg_id=normalized_reg_id,
                semester=data.academic.semester or f"sem{student.semester or 1}",
                cgpa=data.academic.cgpa if data.academic.cgpa is not None else 0,
                credits_completed=data.academic.credits_completed,
            )
            db.add(academic)
        else:
            if data.academic.semester is not None:
                academic.semester = data.academic.semester
            if data.academic.cgpa is not None:
                academic.cgpa = data.academic.cgpa
            if data.academic.credits_completed is not None:
                academic.credits_completed = data.academic.credits_completed

    if data.financial is not None:
        financial = db.query(FinancialRecord).filter(FinancialRecord.reg_id == normalized_reg_id).first()
        if not financial:
            financial = FinancialRecord(reg_id=normalized_reg_id)
            db.add(financial)

        if data.financial.tuition_fee is not None:
            financial.tuition_fee = data.financial.tuition_fee
        if data.financial.paid_amount is not None:
            financial.paid_amount = data.financial.paid_amount
        if data.financial.due_amount is not None:
            financial.due_amount = data.financial.due_amount
        if data.financial.pending_fees is not None:
            financial.pending_fees = data.financial.pending_fees

    if data.cgpa_records is not None:
        db.query(CGPARecord).filter(CGPARecord.reg_id == normalized_reg_id).delete()
        for record in data.cgpa_records:
            db.add(CGPARecord(
                reg_id=normalized_reg_id,
                semester=record.semester,
                cgpa=record.cgpa,
            ))

    if data.courses is not None:
        db.query(StudentCourse).filter(StudentCourse.reg_id == normalized_reg_id).delete()
        for course in data.courses:
            db.add(StudentCourse(
                reg_id=normalized_reg_id,
                course_name=course.course_name,
                marks=course.marks,
            ))

    db.commit()
    db.refresh(student)
    return serialize_student_record(student, db)


@router.get("/mental-health-summary", response_model=AdminMentalHealthSummary)
def get_mental_health_summary(
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    alerts = db.query(MentalHealthAlert).all()
    severities = [(alert.severity or "").lower() for alert in alerts]

    return AdminMentalHealthSummary(
        total_alerts=len(alerts),
        new_alerts=sum(1 for alert in alerts if (alert.status or "new") == "new"),
        critical_alerts=severities.count("critical"),
        high_alerts=severities.count("high"),
        moderate_alerts=severities.count("moderate"),
        low_alerts=severities.count("low"),
    )


@router.get("/mental-health-alerts", response_model=list[MentalHealthAlertResponse])
def list_mental_health_alerts(
    alert_status: str | None = None,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(MentalHealthAlert)
    if alert_status:
        query = query.filter(MentalHealthAlert.status == alert_status.strip().lower())

    alerts = sort_alerts(query.all())
    students = student_lookup_for_alerts(db, alerts)
    return [
        serialize_alert(alert, students.get(alert.reg_id))
        for alert in alerts
    ]


@router.patch("/mental-health-alerts/{alert_id}", response_model=MentalHealthAlertResponse)
def update_mental_health_alert(
    alert_id: int,
    data: MentalHealthAlertUpdate,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    alert = db.query(MentalHealthAlert).filter(MentalHealthAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mental-health alert not found",
        )

    now = datetime.utcnow()
    if data.status is not None:
        alert.status = data.status
        if data.status in {"reviewed", "contacted"} and alert.reviewed_at is None:
            alert.reviewed_at = now
        if data.status == "closed" and alert.closed_at is None:
            alert.closed_at = now

    if data.admin_notes is not None:
        alert.admin_notes = data.admin_notes.strip()

    db.commit()
    db.refresh(alert)

    student = None
    if alert.reg_id:
        student = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == alert.reg_id).first()
    return serialize_alert(alert, student)


@router.get(
    "/students/{reg_id}/mental-health",
    response_model=StudentMentalHealthResponse,
)
def get_student_mental_health(
    reg_id: str,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_reg_id = reg_id.strip().upper()
    student = db.query(AuthorizedUser).filter(AuthorizedUser.reg_id == normalized_reg_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    alerts = sort_alerts(
        db.query(MentalHealthAlert)
        .filter(MentalHealthAlert.reg_id == normalized_reg_id)
        .all()
    )

    return StudentMentalHealthResponse(
        student=student,
        alerts=[serialize_alert(alert, student) for alert in alerts],
    )
