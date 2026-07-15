"""
Production observability test suite.
"""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from observability.cost import CostCalculator
from observability.database import ObservabilityDatabase
from observability.session import SessionTracker


class TestCostCalculation(unittest.TestCase):
    """Test cost calculation engine."""

    def test_normalize_model_names(self):
        """Test model name normalization."""
        self.assertEqual(CostCalculator.normalize_model_name("openai/gpt-4o"), "gpt-4o")
        self.assertEqual(CostCalculator.normalize_model_name("gpt-4o-mini"), "gpt-4o-mini")

    def test_input_cost_gpt4o(self):
        """Test GPT-4o input cost ($15 per MTok)."""
        cost = CostCalculator.calculate_input_cost_cents("gpt-4o", 1_000_000)
        self.assertEqual(cost, 1500)

    def test_output_cost_gpt4o(self):
        """Test GPT-4o output cost ($60 per MTok)."""
        cost = CostCalculator.calculate_output_cost_cents("gpt-4o", 1_000_000)
        self.assertEqual(cost, 6000)


class TestDatabase(unittest.TestCase):
    """Test observability database."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = ObservabilityDatabase(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_creation(self):
        """Test database initializes with required tables."""
        tables = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        self.assertIn("llm_logs", table_names)
        self.assertIn("sessions", table_names)
        self.assertIn("costs", table_names)

    def test_session_creation(self):
        """Test session tracking."""
        tracker = SessionTracker(self.db)
        session_id = tracker.create_session("test-user")

        self.assertIsNotNone(session_id)

        session = self.db.get_latest_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session["query_count"], 0)

    def test_llm_log_insertion(self):
        """Test LLM log insertion."""
        tracker = SessionTracker(self.db)
        session_id = tracker.create_session("test-user")

        self.db.insert(
            """
            INSERT INTO llm_logs 
            (id, session_id, user_id_hash, created_at, model_name, 
             input_tokens, output_tokens, total_tokens, latency_ms, 
             input_cost, output_cost, total_cost, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "log-1",
                session_id,
                "hash123",
                datetime.utcnow().isoformat(),
                "gpt-4o-mini",
                100,
                50,
                150,
                500.0,
                1,
                1,
                2,
                "success",
            ),
        )

        logs = self.db.get_llm_logs(limit=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["model_name"], "gpt-4o-mini")

    def test_cost_tracking(self):
        """Test cost aggregation."""
        tracker = SessionTracker(self.db)
        session_id = tracker.create_session("test-user")

        today = datetime.utcnow().date().isoformat()
        self.db.upsert_cost(
            date=today,
            model_name="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            input_cost=1,
            output_cost=1,
            total_cost=2,
            session_id=session_id,
            user_id_hash="hash123",
        )

        costs = self.db.get_costs(date=today)
        self.assertEqual(len(costs), 1)
        self.assertEqual(costs[0]["total_cost"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
