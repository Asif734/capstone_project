import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.sqldb import Base
from app.db import student_tables  # noqa: F401 - registers models with Base
from app.services.memory_service import MemoryService


class MemoryServiceTests(unittest.TestCase):
    def test_add_get_clear_and_limit_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            service = MemoryService(str(path), max_interactions_per_user=2)

            service.add_interaction("user-1", "one", "answer one")
            service.add_interaction("user-1", "two", "answer two")
            service.add_interaction("user-1", "three", "answer three")

            history = service.get_user_memory("user-1")
            self.assertEqual([item["question"] for item in history], ["two", "three"])
            json.loads(path.read_text(encoding="utf-8"))

            service.clear_user_memory("user-1")
            self.assertEqual(service.get_user_memory("user-1"), [])

    def test_corrupt_file_is_recovered_on_next_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            path.write_text("not-json", encoding="utf-8")
            service = MemoryService(str(path))

            self.assertEqual(service.get_user_memory("user-1"), [])
            service.add_interaction("user-1", "hello", "hi")
            self.assertEqual(service.get_user_memory("user-1")[0]["question"], "hello")

    def test_database_backend_persists_limits_and_clears_history(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        with patch("app.db.sqldb.SessionLocal", test_session):
            service = MemoryService(backend="database", max_interactions_per_user=2)
            service.add_interaction("user-1", "one", "first")
            service.add_interaction("user-1", "two", "second")
            service.add_interaction("user-1", "three", "third")
            self.assertEqual(
                [item["question"] for item in service.get_user_memory("user-1")],
                ["two", "three"],
            )
            service.clear_user_memory("user-1")
            self.assertEqual(service.get_user_memory("user-1"), [])


if __name__ == "__main__":
    unittest.main()
