from __future__ import annotations

from .alerts import AlertEngine
from .ab_testing import ABTestManager
from .cost import CostCalculator
from .database import ObservabilityDatabase
from .evaluation import EvaluationIntegrator
from .exports import ExportService
from .logging import LoggedLLMProxy
from .metrics import MetricsEngine
from .session import SessionTracker


class ObservabilityService:
    def __init__(self, db_path: str = "data/observability.db"):
        self.db = ObservabilityDatabase(db_path)
        self.session_tracker = SessionTracker(self.db)
        self.logger = LoggedLLMProxy(self.db)
        self.cost_calculator = CostCalculator()
        self.alert_engine = AlertEngine(self.db)
        self.metrics = MetricsEngine(self.db)
        self.ab_test = ABTestManager(self.db)
        self.exporter = ExportService(self.db)
        self.evaluator = EvaluationIntegrator(self.db)

    def get_database(self) -> ObservabilityDatabase:
        return self.db

    def create_session(self, user_id: str) -> str:
        return self.session_tracker.create_session(user_id)
