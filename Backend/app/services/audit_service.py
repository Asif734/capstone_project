import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.sqldb import SessionLocal
from app.db.student_tables import AccessAuditLog

logger = logging.getLogger(__name__)


def log_data_access_sync(
    *,
    agent_node: str,
    action_type: str,
    auth_status: str,
    actor_student_id: Optional[str] = None,
    target_student_id: Optional[str] = None,
    token_jti: Optional[str] = None,
    client_ip: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[AccessAuditLog]:
    """
    Synchronous helper to record an immutable FERPA-compliant audit log entry.
    Wrapped in try/except with structured logging; never raises exceptions or
    crashes the main chat turn if database logging fails.

    Guaranteed NO raw PII (names, full chat messages, actual marks/CGPA) is stored.
    """
    try:
        # Sanitize string representations, ensuring empty strings become None
        clean_actor = str(actor_student_id).strip() if actor_student_id is not None and str(actor_student_id).strip() else None
        clean_target = str(target_student_id).strip() if target_student_id is not None and str(target_student_id).strip() else None
        clean_jti = str(token_jti).strip() if token_jti is not None and str(token_jti).strip() else None
        clean_ip = str(client_ip).strip() if client_ip is not None and str(client_ip).strip() else None

        entry = AccessAuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            actor_student_id=clean_actor,
            target_student_id=clean_target,
            agent_node=str(agent_node),
            action_type=str(action_type),
            auth_status=str(auth_status),
            token_jti=clean_jti,
            client_ip=clean_ip,
        )

        if db is not None:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        else:
            with SessionLocal() as session:
                session.add(entry)
                session.commit()
                session.refresh(entry)
                return entry
    except Exception as exc:
        logger.exception(
            "Failed to write FERPA access audit log: agent_node=%s, action_type=%s, auth_status=%s, error=%s",
            agent_node,
            action_type,
            auth_status,
            exc,
        )
        return None


async def log_data_access(
    *,
    agent_node: str,
    action_type: str,
    auth_status: str,
    actor_student_id: Optional[str] = None,
    target_student_id: Optional[str] = None,
    token_jti: Optional[str] = None,
    client_ip: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[AccessAuditLog]:
    """
    Async helper to record an immutable FERPA-compliant audit log entry.
    Dispatches to threadpool to prevent blocking the async event loop.
    """
    return await asyncio.to_thread(
        log_data_access_sync,
        agent_node=agent_node,
        action_type=action_type,
        auth_status=auth_status,
        actor_student_id=actor_student_id,
        target_student_id=target_student_id,
        token_jti=token_jti,
        client_ip=client_ip,
        db=db,
    )


def get_audit_logs(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    actor_student_id: Optional[str] = None,
    target_student_id: Optional[str] = None,
    action_type: Optional[str] = None,
    auth_status: Optional[str] = None,
    agent_node: Optional[str] = None,
) -> Tuple[int, List[AccessAuditLog]]:
    """Query and filter audit logs for administrative inspection."""
    query = db.query(AccessAuditLog)

    if actor_student_id:
        query = query.filter(AccessAuditLog.actor_student_id == actor_student_id.strip())
    if target_student_id:
        query = query.filter(AccessAuditLog.target_student_id == target_student_id.strip())
    if action_type:
        query = query.filter(AccessAuditLog.action_type == action_type.strip())
    if auth_status:
        query = query.filter(AccessAuditLog.auth_status == auth_status.strip())
    if agent_node:
        query = query.filter(AccessAuditLog.agent_node == agent_node.strip())

    total = query.count()
    items = query.order_by(desc(AccessAuditLog.timestamp)).offset(offset).limit(limit).all()
    return total, items

