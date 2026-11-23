import torch
import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.sqldb import Base
from app.db.student_tables import AccessAuditLog, AuthorizedUser
from app.main import app
from app.services.audit_service import (
    get_audit_logs,
    log_data_access,
    log_data_access_sync,
)
from app.utils.graph import auth_required_agent, student_agent


class TestAccessAuditLogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for test isolation
        cls.engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestSessionLocal = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.TestSessionLocal()
        # Clean audit logs between tests
        self.db.query(AccessAuditLog).delete()
        self.db.query(AuthorizedUser).delete()
        self.db.commit()

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def test_log_data_access_sync_creates_entry(self):
        entry = log_data_access_sync(
            agent_node="private_student_agent",
            action_type="READ_CGPA",
            auth_status="AUTHORIZED",
            actor_student_id="202611001",
            target_student_id="202611001",
            token_jti="jti-test-123",
            client_ip="192.168.1.100",
            db=self.db,
        )
        self.assertIsNotNone(entry)
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.agent_node, "private_student_agent")
        self.assertEqual(entry.action_type, "READ_CGPA")
        self.assertEqual(entry.auth_status, "AUTHORIZED")
        self.assertEqual(entry.actor_student_id, "202611001")
        self.assertEqual(entry.target_student_id, "202611001")
        self.assertEqual(entry.token_jti, "jti-test-123")
        self.assertEqual(entry.client_ip, "192.168.1.100")

    def test_log_data_access_async(self):
        async def run_async():
            return await log_data_access(
                agent_node="auth_gate",
                action_type="UNAUTHORIZED_ATTEMPT",
                auth_status="DENIED_UNAUTHENTICATED",
                actor_student_id=None,
                target_student_id="202611099",
                token_jti=None,
                client_ip="10.0.0.5",
            )

        with patch("app.services.audit_service.SessionLocal", self.TestSessionLocal):
            entry = asyncio.run(run_async())

        self.assertIsNotNone(entry)
        self.assertEqual(entry.action_type, "UNAUTHORIZED_ATTEMPT")
        self.assertEqual(entry.auth_status, "DENIED_UNAUTHENTICATED")
        self.assertIsNone(entry.actor_student_id)
        self.assertEqual(entry.target_student_id, "202611099")

    def test_log_data_access_failsafe_does_not_raise(self):
        mock_db = MagicMock()
        mock_db.add.side_effect = RuntimeError("Database connection died")

        # Must not raise exception
        result = log_data_access_sync(
            agent_node="private_student_agent",
            action_type="READ_CGPA",
            auth_status="AUTHORIZED",
            actor_student_id="202611001",
            target_student_id="202611001",
            db=mock_db,
        )
        self.assertIsNone(result)

    def test_auth_gate_node_logs_unauthorized_attempt(self):
        state = {
            "question": "What is the CGPA of student 202611050?",
            "context": None,
            "docs": None,
            "answer": None,
            "route": "auth_required",
            "is_authenticated": False,
            "user_reg_id": None,
            "token_jti": None,
            "client_ip": "127.0.0.1",
            "top_k": 3,
            "conversation_history": None,
            "mental_health_assessment": None,
        }

        with patch("app.services.audit_service.SessionLocal", self.TestSessionLocal):
            res_state = auth_required_agent(state)

        self.assertIn("Please log in", res_state["answer"])

        logs = self.db.query(AccessAuditLog).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].agent_node, "auth_gate")
        self.assertEqual(logs[0].action_type, "UNAUTHORIZED_ATTEMPT")
        self.assertEqual(logs[0].auth_status, "DENIED_UNAUTHENTICATED")
        self.assertEqual(logs[0].target_student_id, "202611050")
        self.assertIsNone(logs[0].actor_student_id)

    def test_private_student_agent_logs_forbidden_when_accessing_other_student(self):
        state = {
            "question": "Can I see marks of 202611099?",
            "context": None,
            "docs": None,
            "answer": None,
            "route": "student",
            "is_authenticated": True,
            "user_reg_id": "202611001",
            "token_jti": "jti-dpop-xyz",
            "client_ip": "172.16.0.2",
            "top_k": 3,
            "conversation_history": None,
            "mental_health_assessment": None,
        }

        with (
            patch("app.db.database.get_db", lambda: iter([self.db])),
            patch("app.services.audit_service.SessionLocal", self.TestSessionLocal),
        ):
            res_state = student_agent(state)

        self.assertIn("private student information", res_state["answer"])

        logs = self.db.query(AccessAuditLog).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].agent_node, "private_student_agent")
        self.assertEqual(logs[0].action_type, "UNAUTHORIZED_ATTEMPT")
        self.assertEqual(logs[0].auth_status, "DENIED_FORBIDDEN")
        self.assertEqual(logs[0].actor_student_id, "202611001")
        self.assertEqual(logs[0].target_student_id, "202611099")
        self.assertEqual(logs[0].token_jti, "jti-dpop-xyz")

    def test_private_student_agent_logs_authorized_read(self):
        # Create student in test db
        user = AuthorizedUser(
            reg_id="202611001",
            name="Test Student",
            email="test@bup.edu.bd",
        )
        self.db.add(user)
        self.db.commit()

        state = {
            "question": "Show my CGPA and semester results",
            "context": None,
            "docs": None,
            "answer": None,
            "route": "student",
            "is_authenticated": True,
            "user_reg_id": "202611001",
            "token_jti": "jti-auth-token-1",
            "client_ip": "192.168.1.50",
            "top_k": 3,
            "conversation_history": None,
            "mental_health_assessment": None,
        }

        with (
            patch("app.db.database.get_db", lambda: iter([self.db])),
            patch("app.db.database.get_student_data_by_reg_id", return_value={"name": "Test", "cgpa": {}}),
            patch("app.utils.graph.student_prompt"),
            patch("app.utils.graph.llm"),
            patch("app.utils.graph.clean_llm_output", return_value="Your CGPA is 3.85"),
        ):
            res_state = student_agent(state)

        logs = self.db.query(AccessAuditLog).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].agent_node, "private_student_agent")
        self.assertEqual(logs[0].action_type, "READ_CGPA")
        self.assertEqual(logs[0].auth_status, "AUTHORIZED")
        self.assertEqual(logs[0].actor_student_id, "202611001")
        self.assertEqual(logs[0].target_student_id, "202611001")
        self.assertEqual(logs[0].token_jti, "jti-auth-token-1")

    def test_admin_audit_logs_endpoint(self):
        # Seed 3 audit entries
        for i, status_val in enumerate(["AUTHORIZED", "DENIED_UNAUTHENTICATED", "DENIED_FORBIDDEN"]):
            entry = AccessAuditLog(
                id=f"id-{i}",
                timestamp=datetime.now(timezone.utc),
                actor_student_id=f"actor-{i}",
                target_student_id=f"target-{i}",
                agent_node="private_student_agent",
                action_type="READ_CGPA",
                auth_status=status_val,
                client_ip="127.0.0.1",
            )
            self.db.add(entry)
        self.db.commit()

        client = TestClient(app)

        # 1. Unauthenticated request should be 401
        res = client.get("/api/admin/audit-logs")
        self.assertEqual(res.status_code, 401)

        # 2. Valid admin token
        admin_token = jwt.encode(
            {"type": "admin", "email": settings.ADMIN_EMAIL},
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        from app.db.database import get_db
        app.dependency_overrides[get_db] = lambda: self.db

        res = client.get(
            "/api/admin/audit-logs",
            headers={"X-Admin-Token": admin_token},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["items"]), 3)

        # Test filtering by auth_status
        res_filtered = client.get(
            "/api/admin/audit-logs?auth_status=DENIED_FORBIDDEN",
            headers={"X-Admin-Token": admin_token},
        )
        self.assertEqual(res_filtered.status_code, 200)
        data_filtered = res_filtered.json()
        self.assertEqual(data_filtered["total"], 1)
        self.assertEqual(data_filtered["items"][0]["auth_status"], "DENIED_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
