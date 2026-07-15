from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cost import CostCalculator
from .database import ObservabilityDatabase
from .utils import count_tokens, hash_text, json_safe, now_iso

logger = logging.getLogger("observability")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


@dataclass
class LoggedLLMCall:
    session_id: str
    user_id: str
    conversation_id: Optional[str] = None
    model_name: str = "openai/gpt-4o-mini"
    id: Optional[str] = None
    db: ObservabilityDatabase | None = None

    start_ts: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    status: str = "pending"
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    tool_used: Optional[str] = None
    retrieved_chunk_count: int = 0
    prompt_version: Optional[str] = None
    embedding_model: Optional[str] = None
    ab_test_variant: Optional[str] = None
    faithfulness_score: Optional[float] = None
    hallucination_score: Optional[float] = None
    toxicity_score: Optional[float] = None
    bias_score: Optional[float] = None
    relevancy_score: Optional[float] = None
    user_message_hash: Optional[str] = None
    user_message_summary: Optional[str] = None

    def __enter__(self) -> "LoggedLLMCall":
        self.start_ts = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.latency_ms = (time.time() - self.start_ts) * 1000.0
        if exc_type:
            self.status = "failure"
            self.error_code = exc_type.__name__
            self.error_message = str(exc_val)
        self.log()
        return False

    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def record_context(
        self,
        tool_used: Optional[str] = None,
        retrieved_chunk_count: int = 0,
        prompt_version: Optional[str] = None,
        embedding_model: Optional[str] = None,
        ab_test_variant: Optional[str] = None,
    ) -> None:
        if tool_used:
            self.tool_used = tool_used
        self.retrieved_chunk_count = retrieved_chunk_count
        if prompt_version:
            self.prompt_version = prompt_version
        if embedding_model:
            self.embedding_model = embedding_model
        if ab_test_variant:
            self.ab_test_variant = ab_test_variant

    def record_evaluation_metrics(
        self,
        faithfulness: Optional[float] = None,
        hallucination: Optional[float] = None,
        toxicity: Optional[float] = None,
        bias: Optional[float] = None,
        relevancy: Optional[float] = None,
    ) -> None:
        if faithfulness is not None:
            self.faithfulness_score = faithfulness
        if hallucination is not None:
            self.hallucination_score = hallucination
        if toxicity is not None:
            self.toxicity_score = toxicity
        if bias is not None:
            self.bias_score = bias
        if relevancy is not None:
            self.relevancy_score = relevancy

    def log(self) -> None:
        if not self.db:
            logger.warning("Observability database not configured. Skipping LLM log.")
            return

        user_id_hash = hashlib.sha256(self.user_id.encode("utf-8")).hexdigest()
        total_cost = self.estimate_cost_cents()
        self.id = hash_text(f"{self.session_id}-{self.user_id}-{now_iso()}")[:36]
        self.db.insert(
           "INSERT INTO llm_logs (id, session_id, conversation_id, user_id_hash, user_message_hash, user_message_summary, created_at, model_name, model_version, input_tokens, output_tokens, total_tokens, latency_ms, input_cost, output_cost, total_cost, status, error_message, error_code, tool_used, retrieved_chunk_count, prompt_version, embedding_model, ab_test_variant, faithfulness_score, hallucination_score, toxicity_score, bias_score, relevancy_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
           (
               self.id,
               self.session_id,
               self.conversation_id,
               user_id_hash,
               self.user_message_hash,
               self.user_message_summary,
               now_iso(),
               self.model_name,
               self.get_model_version(),
               self.input_tokens,
               self.output_tokens,
               self.input_tokens + self.output_tokens,
               self.latency_ms,
               self.calculate_input_cost_cents(),
               self.calculate_output_cost_cents(),
               total_cost,
               self.status,
               self.error_message,
               self.error_code,
               self.tool_used,
               self.retrieved_chunk_count,
               self.prompt_version,
               self.embedding_model,
               self.ab_test_variant,
               self.faithfulness_score,
               self.hallucination_score,
               self.toxicity_score,
               self.bias_score,
               self.relevancy_score,
           ),
        )

        self.db.upsert_cost(
            date=now_iso()[:10],
            model_name=self.model_name,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            input_cost=self.calculate_input_cost_cents(),
            output_cost=self.calculate_output_cost_cents(),
            total_cost=total_cost,
            session_id=self.session_id,
            user_id_hash=user_id_hash,
        )

        self.db.execute(
            "UPDATE sessions SET query_count = query_count + 1, total_latency_ms = total_latency_ms + ?, max_latency_ms = MAX(max_latency_ms, ?), min_latency_ms = COALESCE(MIN(min_latency_ms, ?), ?), total_tokens = total_tokens + ?, total_input_tokens = total_input_tokens + ?, total_output_tokens = total_output_tokens + ?, session_cost = session_cost + ? WHERE id = ?",
            (
                self.latency_ms,
                self.latency_ms,
                self.latency_ms,
                self.latency_ms,
                self.input_tokens + self.output_tokens,
                self.input_tokens,
                self.output_tokens,
                total_cost,
                self.session_id,
            ),
        )

        logger.info(
            "Logged LLM call: %s %s %sms tokens=%s cost=%sc status=%s",
            self.model_name,
            self.get_model_version(),
            round(self.latency_ms, 2),
            self.input_tokens + self.output_tokens,
            total_cost,
            self.status,
        )

    def get_model_version(self) -> str:
        return self.model_name.split("/")[-1]

    def calculate_input_cost_cents(self) -> int:
        return CostCalculator.calculate_input_cost_cents(self.model_name, self.input_tokens)

    def calculate_output_cost_cents(self) -> int:
        return CostCalculator.calculate_output_cost_cents(self.model_name, self.output_tokens)

    def estimate_cost_cents(self) -> int:
        return self.calculate_input_cost_cents() + self.calculate_output_cost_cents()

    def export_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "session_id",
                    "conversation_id",
                    "created_at",
                    "model_name",
                    "model_version",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "latency_ms",
                    "input_cost",
                    "output_cost",
                    "total_cost",
                    "status",
                    "error_message",
                    "tool_used",
                    "retrieved_chunk_count",
                    "prompt_version",
                    "ab_test_variant",
                    "faithfulness_score",
                    "hallucination_score",
                    "bias_score",
                    "toxicity_score",
                    "relevancy_score",
                ],
            )
            writer.writeheader()
            for row in self.db.get_llm_logs():
                writer.writerow({
                    "session_id": row["session_id"],
                    "conversation_id": row["conversation_id"],
                    "created_at": row["created_at"],
                    "model_name": row["model_name"],
                    "model_version": row["model_version"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                    "total_tokens": row["total_tokens"],
                    "latency_ms": row["latency_ms"],
                    "input_cost": row["input_cost"],
                    "output_cost": row["output_cost"],
                    "total_cost": row["total_cost"],
                    "status": row["status"],
                    "error_message": row["error_message"],
                    "tool_used": row["tool_used"],
                    "retrieved_chunk_count": row["retrieved_chunk_count"],
                    "prompt_version": row["prompt_version"],
                    "ab_test_variant": row["ab_test_variant"],
                    "faithfulness_score": row["faithfulness_score"],
                    "hallucination_score": row["hallucination_score"],
                    "bias_score": row["bias_score"],
                    "toxicity_score": row["toxicity_score"],
                    "relevancy_score": row["relevancy_score"],
                })


class LoggedLLMProxy:
    """Proxy for wrapping LLM calls in a context manager for logging."""

    def __init__(self, db: ObservabilityDatabase):
        self.db = db

    def create_call(self, session_id: str, user_id: str, conversation_id: Optional[str] = None, model_name: Optional[str] = None) -> LoggedLLMCall:
        return LoggedLLMCall(
            session_id=session_id,
            user_id=user_id,
            conversation_id=conversation_id,
            model_name=model_name or "openai/gpt-4o-mini",
            db=self.db,
        )
