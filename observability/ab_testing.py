from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from .database import ObservabilityDatabase
from .utils import hash_text, now_iso


class ABTestManager:
    """Manages prompt versions and A/B traffic allocation."""

    def __init__(self, db: ObservabilityDatabase):
        self.db = db

    def create_prompt_version(self, version_name: str, prompt_type: str, prompt_text: str, active: bool = False) -> str:
        version_id = str(uuid.uuid4())
        prompt_hash = hash_text(prompt_text)
        self.db.insert(
            "INSERT INTO prompt_versions (id, version_name, version_number, prompt_type, prompt_hash, is_active, created_at, activated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                version_id,
                version_name,
                self._next_version_number(prompt_type),
                prompt_type,
                prompt_hash,
                1 if active else 0,
                now_iso(),
                now_iso() if active else None,
            ),
        )
        return version_id

    def _next_version_number(self, prompt_type: str) -> int:
        existing = self.db.fetch_one("SELECT MAX(version_number) as max_num FROM prompt_versions WHERE prompt_type = ?", (prompt_type,))
        return (existing["max_num"] or 0) + 1

    def get_active_prompt_version(self, prompt_type: str) -> Optional[dict[str, Any]]:
        row = self.db.fetch_one("SELECT * FROM prompt_versions WHERE prompt_type = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1", (prompt_type,))
        return self.db.as_dict(row) if row else None

    def select_variant(self, experiment_id: str) -> str:
        experiment = self.db.fetch_one("SELECT * FROM prompt_experiments WHERE id = ?", (experiment_id,))
        if not experiment:
            raise ValueError("Experiment not found")
        if experiment["traffic_split_percentage"] >= 50:
            return "A" if uuid.uuid4().int % 100 < experiment["traffic_split_percentage"] else "B"
        return "A" if uuid.uuid4().int % 100 < experiment["traffic_split_percentage"] else "B"

    def create_experiment(self, name: str, description: str, variant_a_id: str, variant_b_id: str, traffic_split_percentage: int = 50) -> str:
        experiment_id = str(uuid.uuid4())
        self.db.insert(
            "INSERT INTO prompt_experiments (id, name, description, variant_a_id, variant_b_id, started_at, status, traffic_split_percentage) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                experiment_id,
                name,
                description,
                variant_a_id,
                variant_b_id,
                now_iso(),
                "running",
                traffic_split_percentage,
            ),
        )
        return experiment_id

    def complete_experiment(self, experiment_id: str, winner_variant: str, winner_metric: str) -> None:
        self.db.execute(
            "UPDATE prompt_experiments SET ended_at = ?, status = ?, winner_variant = ?, winner_metric = ? WHERE id = ?",
            (now_iso(), "completed", winner_variant, winner_metric, experiment_id),
        )

    def record_call(self, prompt_version: str, latency_ms: float, total_cost: int, faithfulness: float | None = None, hallucination: float | None = None) -> None:
        row = self.db.fetch_one(
            "SELECT total_calls, avg_latency_ms, avg_cost, avg_faithfulness, avg_hallucination FROM prompt_versions WHERE version_name = ?",
            (prompt_version,),
        )
        if not row:
            return

        previous_calls = row["total_calls"] or 0
        new_calls = previous_calls + 1
        avg_latency = ((row["avg_latency_ms"] or 0.0) * previous_calls + latency_ms) / new_calls
        avg_cost = ((row["avg_cost"] or 0.0) * previous_calls + total_cost) / new_calls
        avg_faithfulness = ((row["avg_faithfulness"] or 0.0) * previous_calls + (faithfulness or 0.0)) / new_calls
        avg_hallucination = ((row["avg_hallucination"] or 0.0) * previous_calls + (hallucination or 0.0)) / new_calls

        self.db.execute(
            "UPDATE prompt_versions SET total_calls = ?, avg_latency_ms = ?, avg_cost = ?, avg_faithfulness = ?, avg_hallucination = ? WHERE version_name = ?",
            (
                new_calls,
                avg_latency,
                avg_cost,
                avg_faithfulness,
                avg_hallucination,
                prompt_version,
            ),
        )

    def get_experiments(self) -> list[dict[str, Any]]:
        return [self.db.as_dict(row) for row in self.db.fetch_all("SELECT * FROM prompt_experiments ORDER BY started_at DESC")]
