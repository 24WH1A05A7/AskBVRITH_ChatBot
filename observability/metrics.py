from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .database import ObservabilityDatabase


class MetricsEngine:
    """Pre-calculates dashboard metrics from observability data."""

    def __init__(self, db: ObservabilityDatabase):
        self.db = db

    def get_live_metrics(self) -> dict[str, Any]:
        total_users = len({row["user_id_hash"] for row in self.db.fetch_all("SELECT user_id_hash FROM sessions")})
        total_sessions = len(self.db.fetch_all("SELECT id FROM sessions"))
        total_tokens = sum(row["total_tokens"] for row in self.db.fetch_all("SELECT total_tokens FROM llm_logs"))
        total_cost = sum(row["total_cost"] for row in self.db.fetch_all("SELECT total_cost FROM llm_logs")) / 100.0
        query_count = len(self.db.fetch_all("SELECT id FROM llm_logs"))
        errors = len(self.db.fetch_all("SELECT id FROM llm_logs WHERE status = 'failure'"))
        avg_latency = self._safe_average([row["latency_ms"] for row in self.db.fetch_all("SELECT latency_ms FROM llm_logs")])
        p95_latency = self._percentile([row["latency_ms"] for row in self.db.fetch_all("SELECT latency_ms FROM llm_logs")], 95)
        p99_latency = self._percentile([row["latency_ms"] for row in self.db.fetch_all("SELECT latency_ms FROM llm_logs")], 99)
        avg_tokens = self._safe_average([row["total_tokens"] for row in self.db.fetch_all("SELECT total_tokens FROM llm_logs")])
        avg_cost = total_cost / query_count if query_count else 0.0
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "query_count": query_count,
            "error_rate": errors / query_count if query_count else 0.0,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
            "avg_tokens": avg_tokens,
            "avg_cost": avg_cost,
        }

    def _safe_average(self, values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _percentile(self, values: List[float], percentile: int) -> float:
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = min(len(values) - 1, max(0, int(round((percentile / 100) * len(values))) - 1))
        return sorted_values[index]

    def get_alert_metrics(self) -> dict[str, Any]:
        return {
            "active_alerts": len(self.db.fetch_all("SELECT id FROM alerts WHERE acknowledged = 0")),
            "alert_history": len(self.db.fetch_all("SELECT id FROM alerts")),
        }

    def get_cost_trends(self) -> list[dict[str, Any]]:
        return [self.db.as_dict(row) for row in self.db.get_costs()]

    def get_model_usage(self) -> list[dict[str, Any]]:
        return [self.db.as_dict(row) for row in self.db.fetch_all("SELECT model_name, COUNT(*) as usage_count FROM llm_logs GROUP BY model_name ORDER BY usage_count DESC")] 

    def get_prompt_version_usage(self) -> list[dict[str, Any]]:
        return [self.db.as_dict(row) for row in self.db.fetch_all("SELECT prompt_version, COUNT(*) as usage_count FROM llm_logs GROUP BY prompt_version ORDER BY usage_count DESC")] 
