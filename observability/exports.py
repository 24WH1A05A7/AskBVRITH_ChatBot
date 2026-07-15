from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database import ObservabilityDatabase


class ExportService:
    """Export observability and evaluation data in CSV, JSONL, and report formats."""

    def __init__(self, db: ObservabilityDatabase):
        self.db = db

    def export_logs_csv(self, target_path: Path) -> None:
        self.db.export_table_to_csv("llm_logs", target_path)

    def export_logs_jsonl(self, target_path: Path) -> None:
        self.db.export_table_to_jsonl("llm_logs", target_path)

    def export_metrics_csv(self, target_path: Path) -> None:
        self.db.export_table_to_csv("metrics", target_path)

    def export_evaluation_report(self, report: dict[str, Any], target_path: Path) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    def export_alerts_csv(self, target_path: Path) -> None:
        self.db.export_table_to_csv("alerts", target_path)
