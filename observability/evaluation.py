from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from .database import ObservabilityDatabase


class EvaluationIntegrator:
    """Integrates external evaluation reports and stores scores."""

    def __init__(self, db: ObservabilityDatabase):
        self.db = db

    def store_report(
        self,
        llm_log_id: Optional[str],
        framework: str,
        faithfulness: Optional[float],
        bias: Optional[float],
        hallucination: Optional[float],
        toxicity: Optional[float],
        relevancy: Optional[float],
        report_json: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.db.add_evaluation_report(
            llm_log_id=llm_log_id,
            framework=framework,
            faithfulness=faithfulness,
            bias=bias,
            hallucination=hallucination,
            toxicity=toxicity,
            relevancy=relevancy,
            report_json=report_json,
        )

    def load_reports(self) -> list[dict[str, Any]]:
        return [self.db.as_dict(row) for row in self.db.fetch_all("SELECT * FROM evaluation_reports ORDER BY created_at DESC")]
