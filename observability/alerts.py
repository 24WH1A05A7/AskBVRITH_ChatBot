from __future__ import annotations

import json
import os
import requests
from datetime import datetime
from typing import Any, Dict, Optional

from .database import ObservabilityDatabase
from .utils import now_iso


class AlertEngine:
    """Alerting rules, storage, and external notification integration."""

    DEFAULT_THRESHOLDS: dict[str, dict[str, Any]] = {
        "latency_ms": {"threshold": 10000.0, "severity": "critical", "label": "Latency"},
        "error_rate": {"threshold": 0.05, "severity": "high", "label": "Error Rate"},
        "cost_per_query": {"threshold": 0.10, "severity": "medium", "label": "Cost per Query"},
        "faithfulness_score": {"threshold": 0.8, "severity": "medium", "label": "Faithfulness"},
        "hallucination_score": {"threshold": 0.3, "severity": "medium", "label": "Hallucination"},
        "bias_score": {"threshold": 0.2, "severity": "medium", "label": "Bias"},
        "toxicity_score": {"threshold": 0.1, "severity": "medium", "label": "Toxicity"},
    }

    def __init__(self, db: ObservabilityDatabase, slack_webhook_url: str | None = None, email_recipient: str | None = None):
        self.db = db
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.email_recipient = email_recipient or os.getenv("ALERT_EMAIL_RECIPIENT")

    def evaluate(self, metrics: dict[str, Any], session_id: str | None = None, llm_log_id: str | None = None) -> list[dict[str, Any]]:
        alerts = []
        if metrics.get("latency_ms") and metrics["latency_ms"] > self.DEFAULT_THRESHOLDS["latency_ms"]["threshold"]:
            alerts.append(self._create_alert("latency_ms", metrics["latency_ms"], session_id, llm_log_id))
        if metrics.get("error_rate") and metrics["error_rate"] > self.DEFAULT_THRESHOLDS["error_rate"]["threshold"]:
            alerts.append(self._create_alert("error_rate", metrics["error_rate"], session_id, llm_log_id))
        if metrics.get("cost_per_query") and metrics["cost_per_query"] > self.DEFAULT_THRESHOLDS["cost_per_query"]["threshold"]:
            alerts.append(self._create_alert("cost_per_query", metrics["cost_per_query"], session_id, llm_log_id))
        if metrics.get("faithfulness_score") is not None and metrics["faithfulness_score"] < self.DEFAULT_THRESHOLDS["faithfulness_score"]["threshold"]:
            alerts.append(self._create_alert("faithfulness_score", metrics["faithfulness_score"], session_id, llm_log_id))
        if metrics.get("hallucination_score") is not None and metrics["hallucination_score"] > self.DEFAULT_THRESHOLDS["hallucination_score"]["threshold"]:
            alerts.append(self._create_alert("hallucination_score", metrics["hallucination_score"], session_id, llm_log_id))
        if metrics.get("bias_score") is not None and metrics["bias_score"] > self.DEFAULT_THRESHOLDS["bias_score"]["threshold"]:
            alerts.append(self._create_alert("bias_score", metrics["bias_score"], session_id, llm_log_id))
        if metrics.get("toxicity_score") is not None and metrics["toxicity_score"] > self.DEFAULT_THRESHOLDS["toxicity_score"]["threshold"]:
            alerts.append(self._create_alert("toxicity_score", metrics["toxicity_score"], session_id, llm_log_id))

        for alert in alerts:
            self._store_alert(alert)
            self._notify_external(alert)
        return alerts

    def _create_alert(self, threshold_name: str, actual_value: float, session_id: str | None, llm_log_id: str | None) -> dict[str, Any]:
        threshold = self.DEFAULT_THRESHOLDS[threshold_name]
        message = (
            f"{threshold['label']} threshold breached: "
            f"actual={actual_value} threshold={threshold['threshold']}"
        )
        return {
            "id": now_iso() + threshold_name,
            "created_at": now_iso(),
            "alert_type": threshold_name,
            "severity": threshold["severity"],
            "acknowledged": 0,
            "threshold_name": threshold_name,
            "threshold_value": threshold["threshold"],
            "actual_value": actual_value,
            "message": message,
            "session_id": session_id,
            "llm_log_id": llm_log_id,
            "slack_sent": 0,
            "email_sent": 0,
        }

    def _store_alert(self, alert: dict[str, Any]) -> None:
        self.db.insert(
            "INSERT INTO alerts (id, created_at, acknowledged_at, alert_type, severity, acknowledged, threshold_name, threshold_value, actual_value, message, session_id, llm_log_id, slack_sent, email_sent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                alert["id"],
                alert["created_at"],
                None,
                alert["alert_type"],
                alert["severity"],
                alert["acknowledged"],
                alert["threshold_name"],
                alert["threshold_value"],
                alert["actual_value"],
                alert["message"],
                alert["session_id"],
                alert["llm_log_id"],
                alert["slack_sent"],
                alert["email_sent"],
            ),
        )

    def _notify_external(self, alert: dict[str, Any]) -> None:
        if self.slack_webhook_url:
            try:
                payload = {
                    "text": f"[BVRIT AI Alert] {alert['severity'].upper()} - {alert['message']}"
                }
                resp = requests.post(self.slack_webhook_url, json=payload, timeout=5)
                if resp.ok:
                    self.db.execute("UPDATE alerts SET slack_sent = 1 WHERE id = ?", (alert["id"],))
            except Exception:
                pass

        if self.email_recipient:
            try:
                subject = f"BVRIT AI Alert: {alert['severity'].upper()}"
                body = f"{alert['message']}\n\nSession: {alert['session_id']}\nLog: {alert['llm_log_id']}"
                message = {
                    "subject": subject,
                    "body": body,
                    "to": [self.email_recipient],
                }
                requests.post(
                    os.getenv("EMAIL_NOTIFICATION_URL", ""),
                    json=message,
                    timeout=5,
                )
                self.db.execute("UPDATE alerts SET email_sent = 1 WHERE id = ?", (alert["id"],))
            except Exception:
                pass
