from __future__ import annotations

import csv
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class ObservabilityDatabase:
    """Lightweight SQLite database for observability and analytics."""

    def __init__(self, path: Path | str = "data/observability.db"):
        self.db_path = Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _initialize(self) -> None:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id_hash TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    query_count INTEGER DEFAULT 0,
                    total_latency_ms REAL DEFAULT 0.0,
                    max_latency_ms REAL DEFAULT 0.0,
                    min_latency_ms REAL,
                    total_tokens INTEGER DEFAULT 0,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    session_cost INTEGER DEFAULT 0,
                    primary_model TEXT,
                    memory_usage_mb REAL
                );

                CREATE TABLE IF NOT EXISTS llm_logs (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    conversation_id TEXT,
                    user_id_hash TEXT NOT NULL,
                    user_message_hash TEXT,
                    user_message_summary TEXT,
                    created_at TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_version TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    latency_ms REAL DEFAULT 0.0,
                    input_cost INTEGER DEFAULT 0,
                    output_cost INTEGER DEFAULT 0,
                    total_cost INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    error_code TEXT,
                    tool_used TEXT,
                    retrieved_chunk_count INTEGER DEFAULT 0,
                    prompt_version TEXT,
                    embedding_model TEXT,
                    ab_test_variant TEXT,
                    faithfulness_score REAL,
                    hallucination_score REAL,
                    toxicity_score REAL,
                    bias_score REAL,
                    relevancy_score REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE INDEX IF NOT EXISTS ix_llm_logs_session_id ON llm_logs(session_id);
                CREATE INDEX IF NOT EXISTS ix_llm_logs_user_id_hash ON llm_logs(user_id_hash);
                CREATE INDEX IF NOT EXISTS ix_llm_logs_conversation_id ON llm_logs(conversation_id);
                CREATE INDEX IF NOT EXISTS ix_llm_logs_created_at ON llm_logs(created_at);
                CREATE INDEX IF NOT EXISTS ix_llm_logs_status ON llm_logs(status);

                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    threshold_name TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    actual_value REAL NOT NULL,
                    message TEXT NOT NULL,
                    session_id TEXT,
                    llm_log_id TEXT,
                    slack_sent INTEGER DEFAULT 0,
                    email_sent INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS ix_alerts_alert_type ON alerts(alert_type);
                CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts(created_at);
                CREATE INDEX IF NOT EXISTS ix_alerts_acknowledged ON alerts(acknowledged);

                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id TEXT PRIMARY KEY,
                    version_name TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    prompt_type TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    activated_at TEXT,
                    deactivated_at TEXT,
                    total_calls INTEGER DEFAULT 0,
                    avg_latency_ms REAL,
                    avg_cost REAL,
                    avg_faithfulness REAL,
                    avg_hallucination REAL
                );

                CREATE INDEX IF NOT EXISTS ix_prompt_versions_active ON prompt_versions(is_active);

                CREATE TABLE IF NOT EXISTS prompt_experiments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    variant_a_id TEXT NOT NULL,
                    variant_b_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT NOT NULL,
                    traffic_split_percentage INTEGER DEFAULT 50,
                    winner_variant TEXT,
                    winner_metric TEXT
                );

                CREATE INDEX IF NOT EXISTS ix_prompt_experiments_status ON prompt_experiments(status);

                CREATE TABLE IF NOT EXISTS costs (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    input_cost INTEGER DEFAULT 0,
                    output_cost INTEGER DEFAULT 0,
                    total_cost INTEGER DEFAULT 0,
                    session_id TEXT,
                    user_id_hash TEXT
                );

                CREATE INDEX IF NOT EXISTS ix_costs_model_name ON costs(model_name);
                CREATE INDEX IF NOT EXISTS ix_costs_date ON costs(date);
                CREATE INDEX IF NOT EXISTS ix_costs_session_id ON costs(session_id);

                CREATE TABLE IF NOT EXISTS metrics (
                    id TEXT PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    granularity TEXT NOT NULL,
                    model_name TEXT
                );

                CREATE INDEX IF NOT EXISTS ix_metrics_metric_name ON metrics(metric_name);
                CREATE INDEX IF NOT EXISTS ix_metrics_timestamp ON metrics(timestamp);

                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    llm_log_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    helpful INTEGER,
                    feedback_text TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS ix_feedback_llm_log_id ON feedback(llm_log_id);
                CREATE INDEX IF NOT EXISTS ix_feedback_created_at ON feedback(created_at);

                CREATE TABLE IF NOT EXISTS evaluation_reports (
                    id TEXT PRIMARY KEY,
                    llm_log_id TEXT,
                    framework TEXT NOT NULL,
                    faithfulness REAL,
                    bias REAL,
                    hallucination REAL,
                    toxicity REAL,
                    relevancy REAL,
                    report_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS ix_evaluation_reports_llm_log_id ON evaluation_reports(llm_log_id);
                CREATE INDEX IF NOT EXISTS ix_evaluation_reports_created_at ON evaluation_reports(created_at);
                """
            )
            conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def insert(self, query: str, params: tuple) -> None:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def insert_many(self, query: str, params_list: Iterable[tuple]) -> None:
        with closing(self._connect()) as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

    def export_table_to_csv(self, table_name: str, target_path: Path) -> None:
        rows = self.fetch_all(f"SELECT * FROM {table_name}")
        if not rows:
            return
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(rows[0].keys())
            for row in rows:
                writer.writerow([row[k] for k in row.keys()])

    def export_table_to_jsonl(self, table_name: str, target_path: Path) -> None:
        rows = self.fetch_all(f"SELECT * FROM {table_name}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps({k: row[k] for k in row.keys()}, default=str) + "\n")

    def upsert_cost(self, date: str, model_name: str, input_tokens: int, output_tokens: int, input_cost: int, output_cost: int, total_cost: int, session_id: str, user_id_hash: str) -> None:
        existing = self.fetch_one(
            "SELECT id, input_tokens, output_tokens, input_cost, output_cost, total_cost, request_count FROM costs WHERE date = ? AND model_name = ? AND session_id = ?",
            (date, model_name, session_id),
        )
        if existing:
            self.execute(
                "UPDATE costs SET input_tokens = ?, output_tokens = ?, input_cost = ?, output_cost = ?, total_cost = ?, request_count = ?, user_id_hash = ? WHERE id = ?",
                (
                    existing["input_tokens"] + input_tokens,
                    existing["output_tokens"] + output_tokens,
                    existing["input_cost"] + input_cost,
                    existing["output_cost"] + output_cost,
                    existing["total_cost"] + total_cost,
                    existing["request_count"] + 1,
                    user_id_hash,
                    existing["id"],
                ),
            )
            return
        self.insert(
            "INSERT INTO costs (id, date, model_name, input_tokens, output_tokens, request_count, input_cost, output_cost, total_cost, session_id, user_id_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(datetime.utcnow().timestamp()) + model_name, date, model_name, input_tokens, output_tokens, 1, input_cost, output_cost, total_cost, session_id, user_id_hash),
        )

    def get_latest_session(self, session_id: str) -> Optional[sqlite3.Row]:
        return self.fetch_one("SELECT * FROM sessions WHERE id = ?", (session_id,))

    def get_sessions(self) -> List[sqlite3.Row]:
        return self.fetch_all("SELECT * FROM sessions ORDER BY started_at DESC")

    def get_llm_logs(self, limit: int = 500) -> List[sqlite3.Row]:
        return self.fetch_all("SELECT * FROM llm_logs ORDER BY created_at DESC LIMIT ?", (limit,))

    def get_alerts(self, limit: int = 200) -> List[sqlite3.Row]:
        return self.fetch_all("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))

    def get_prompt_versions(self) -> List[sqlite3.Row]:
        return self.fetch_all("SELECT * FROM prompt_versions ORDER BY created_at DESC")

    def get_active_prompt_version(self) -> Optional[sqlite3.Row]:
        return self.fetch_one("SELECT * FROM prompt_versions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1")

    def get_active_experiment(self) -> Optional[sqlite3.Row]:
        return self.fetch_one("SELECT * FROM prompt_experiments WHERE status = 'running' ORDER BY started_at DESC LIMIT 1")

    def get_costs(self, model_name: Optional[str] = None, date: Optional[str] = None) -> List[sqlite3.Row]:
        query = "SELECT * FROM costs"
        params: list[Any] = []
        if model_name and date:
            query += " WHERE model_name = ? AND date = ?"
            params = [model_name, date]
        elif model_name:
            query += " WHERE model_name = ?"
            params = [model_name]
        elif date:
            query += " WHERE date = ?"
            params = [date]
        query += " ORDER BY date DESC"
        return self.fetch_all(query, tuple(params))

    def get_metrics(self, granularity: Optional[str] = None) -> List[sqlite3.Row]:
        query = "SELECT * FROM metrics"
        params: tuple = ()
        if granularity:
            query += " WHERE granularity = ?"
            params = (granularity,)
        query += " ORDER BY timestamp DESC"
        return self.fetch_all(query, params)

    def insert_metric(self, metric_name: str, value: float, granularity: str, model_name: Optional[str] = None) -> None:
        self.insert(
            "INSERT INTO metrics (id, metric_name, value, timestamp, granularity, model_name) VALUES (?, ?, ?, ?, ?, ?)",
            (str(datetime.utcnow().timestamp()) + metric_name, metric_name, value, datetime.utcnow().isoformat(), granularity, model_name),
        )

    def add_feedback(self, llm_log_id: str, rating: int, helpful: Optional[bool] = None, feedback_text: Optional[str] = None) -> None:
        self.insert(
            "INSERT INTO feedback (id, llm_log_id, rating, helpful, feedback_text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(datetime.utcnow().timestamp()) + llm_log_id, llm_log_id, rating, 1 if helpful else 0 if helpful is not None else None, feedback_text, datetime.utcnow().isoformat()),
        )

    def add_evaluation_report(self, llm_log_id: Optional[str], framework: str, faithfulness: Optional[float], bias: Optional[float], hallucination: Optional[float], toxicity: Optional[float], relevancy: Optional[float], report_json: Optional[Dict[str, Any]] = None) -> None:
        self.insert(
            "INSERT INTO evaluation_reports (id, llm_log_id, framework, faithfulness, bias, hallucination, toxicity, relevancy, report_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(datetime.utcnow().timestamp()) + framework,
                llm_log_id,
                framework,
                faithfulness,
                bias,
                hallucination,
                toxicity,
                relevancy,
                json.dumps(report_json or {}, default=str),
                datetime.utcnow().isoformat(),
            ),
        )

    def as_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {k: row[k] for k in row.keys()}


_default_observability_db: Optional[ObservabilityDatabase] = None


def get_observability_database(path: str = "data/observability.db") -> ObservabilityDatabase:
    global _default_observability_db
    if _default_observability_db is None:
        _default_observability_db = ObservabilityDatabase(path)
    return _default_observability_db
