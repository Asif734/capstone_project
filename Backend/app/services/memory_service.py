import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEMORY_FILE = str(PROJECT_ROOT / "chat_memory.json")
_MEMORY_LOCK = threading.RLock()

class MemoryService:
    """Small, thread-safe JSON chat store for single-process local deployments.

    Production deployments should replace this with a database-backed store so
    multiple application processes can share conversation history.
    """

    def __init__(
        self,
        file_path: str | None = None,
        max_interactions_per_user: int | None = None,
        backend: str | None = None,
    ):
        self.backend = "json" if file_path is not None else (backend or settings.CHAT_MEMORY_BACKEND)
        if self.backend not in {"json", "database"}:
            raise ValueError("Memory backend must be 'json' or 'database'")
        self.file_path = Path(file_path or MEMORY_FILE)
        self.max_interactions_per_user = max(
            1,
            max_interactions_per_user or settings.CHAT_MEMORY_MAX_INTERACTIONS,
        )
        if self.backend == "database":
            return
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with _MEMORY_LOCK:
            if not self.file_path.exists():
                self._save_memory({})

    def _load_memory(self) -> Dict[str, List[Dict]]:
        """Load memory safely, even if file is empty or corrupted."""
        with _MEMORY_LOCK:
            if not self.file_path.exists():
                return {}
            try:
                content = self.file_path.read_text(encoding="utf-8").strip()
                if not content:
                    return {}
                memory = json.loads(content)
                return memory if isinstance(memory, dict) else {}
            except (OSError, json.JSONDecodeError):
                return {}

    def _save_memory(self, memory: Dict[str, List[Dict]]):
        with _MEMORY_LOCK:
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.file_path.parent,
                    prefix=f".{self.file_path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temp_file:
                    json.dump(memory, temp_file, indent=2, ensure_ascii=False)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                    temp_path = Path(temp_file.name)
                os.replace(temp_path, self.file_path)
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink()

    def add_interaction(self, user_id: str, question: str, answer: str):
        if self.backend == "database":
            self._add_database_interaction(user_id, question, answer)
            return
        with _MEMORY_LOCK:
            memory = self._load_memory()
            interactions = memory.setdefault(str(user_id), [])
            interactions.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "question": question,
                "answer": answer,
            })
            memory[str(user_id)] = interactions[-self.max_interactions_per_user:]
            self._save_memory(memory)

    def get_user_memory(self, user_id: str) -> List[Dict]:
        if self.backend == "database":
            return self._get_database_memory(user_id)
        with _MEMORY_LOCK:
            memory = self._load_memory()
            return list(memory.get(str(user_id), []))

    def clear_user_memory(self, user_id: str):
        if self.backend == "database":
            self._clear_database_memory(user_id)
            return
        with _MEMORY_LOCK:
            memory = self._load_memory()
            if str(user_id) in memory:
                memory[str(user_id)] = []
                self._save_memory(memory)

    def _add_database_interaction(self, user_id: str, question: str, answer: str) -> None:
        from app.db.sqldb import SessionLocal
        from app.db.student_tables import ChatInteraction

        with SessionLocal() as db:
            db.add(ChatInteraction(user_key=str(user_id), question=question, answer=answer))
            db.flush()
            stale_ids = [
                row[0]
                for row in (
                    db.query(ChatInteraction.id)
                    .filter(ChatInteraction.user_key == str(user_id))
                    .order_by(ChatInteraction.created_at.desc(), ChatInteraction.id.desc())
                    .offset(self.max_interactions_per_user)
                    .all()
                )
            ]
            if stale_ids:
                db.query(ChatInteraction).filter(ChatInteraction.id.in_(stale_ids)).delete(
                    synchronize_session=False
                )
            db.commit()

    def _get_database_memory(self, user_id: str) -> List[Dict]:
        from app.db.sqldb import SessionLocal
        from app.db.student_tables import ChatInteraction

        with SessionLocal() as db:
            records = (
                db.query(ChatInteraction)
                .filter(ChatInteraction.user_key == str(user_id))
                .order_by(ChatInteraction.created_at.desc(), ChatInteraction.id.desc())
                .limit(self.max_interactions_per_user)
                .all()
            )
            return [
                {
                    "timestamp": self._as_utc_iso(record.created_at),
                    "question": record.question,
                    "answer": record.answer,
                }
                for record in reversed(records)
            ]

    @staticmethod
    def _as_utc_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()

    def _clear_database_memory(self, user_id: str) -> None:
        from app.db.sqldb import SessionLocal
        from app.db.student_tables import ChatInteraction

        with SessionLocal() as db:
            db.query(ChatInteraction).filter(
                ChatInteraction.user_key == str(user_id)
            ).delete(synchronize_session=False)
            db.commit()
