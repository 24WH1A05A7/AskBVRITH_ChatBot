from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .database import ObservabilityDatabase
from .utils import hash_text, now_iso


@dataclass
class SessionTracker:
    db: ObservabilityDatabase

    def create_session(self, user_id: str, conversation_id: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        self.db.insert(
            "INSERT INTO sessions (id, user_id_hash, started_at, primary_model) VALUES (?, ?, ?, ?)",
            (
                session_id,
                hashlib.sha256(user_id.encode("utf-8")).hexdigest(),
                now_iso(),
                None,
            ),
        )
        return session_id

    def end_session(self, session_id: str) -> None:
        self.db.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?", (now_iso(), session_id)
        )

    def set_primary_model(self, session_id: str, model_name: str) -> None:
        self.db.execute(
            "UPDATE sessions SET primary_model = ? WHERE id = ?",
            (model_name, session_id),
        )

    def record_memory(self, session_id: str, memory_usage_mb: float) -> None:
        self.db.execute(
            "UPDATE sessions SET memory_usage_mb = ? WHERE id = ?", (memory_usage_mb, session_id)
        )

    def get_session_stats(self, session_id: str) -> Optional[dict]:
        row = self.db.get_latest_session(session_id)
        return self.db.as_dict(row) if row else None
