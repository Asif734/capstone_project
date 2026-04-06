import os
import json
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEMORY_FILE = str(PROJECT_ROOT / "chat_memory.json")

class MemoryService:
    """Service to handle per-user chat memory."""

    def __init__(self, file_path: str = MEMORY_FILE):
        self.file_path = file_path
        # Ensure file exists
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    def _load_memory(self) -> Dict[str, List[Dict]]:
        """Load memory safely, even if file is empty or corrupted."""
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def _save_memory(self, memory: Dict[str, List[Dict]]):
        with open(self.file_path, "w") as f:
            json.dump(memory, f, indent=2)

    def add_interaction(self, user_id: str, question: str, answer: str):
        memory = self._load_memory()
        if user_id not in memory:
            memory[user_id] = []

        memory[user_id].append({
            "question": question,
            "answer": answer
        })

        self._save_memory(memory)

    def get_user_memory(self, user_id: str) -> List[Dict]:
        memory = self._load_memory()
        return memory.get(user_id, [])

    def clear_user_memory(self, user_id: str):
        memory = self._load_memory()
        if user_id in memory:
            memory[user_id] = []
            self._save_memory(memory)
