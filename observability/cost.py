from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class CostCalculator:
    """Estimates LLM pricing in cents per token for logging and cost dashboards."""

    MODEL_PRICING: ClassVar[dict[str, dict[str, float]]] = {
        "gpt-4o": {"input": 0.0020, "output": 0.0020},
        "gpt-4o-mini": {"input": 0.0010, "output": 0.0010},
        "gpt-5": {"input": 0.0030, "output": 0.0030},
        "text-embedding-3-small": {"input": 0.0004, "output": 0.0004},
        "text-embedding-3-large": {"input": 0.0016, "output": 0.0016},
    }

    @classmethod
    def normalize_model_name(cls, model_name: str) -> str:
        clean = model_name.lower().replace("openai/", "").replace("openrouter/", "")
        if clean.startswith("gpt-5"):
            return "gpt-5"
        if clean.startswith("gpt-4o-mini"):
            return "gpt-4o-mini"
        if clean.startswith("gpt-4o"):
            return "gpt-4o"
        return clean

    @classmethod
    def calculate_input_cost(cls, model_name: str, input_tokens: int) -> float:
        model = cls.normalize_model_name(model_name)
        pricing = cls.MODEL_PRICING.get(model, cls.MODEL_PRICING["gpt-4o-mini"])
        return round(pricing["input"] * input_tokens, 6)

    @classmethod
    def calculate_output_cost(cls, model_name: str, output_tokens: int) -> float:
        model = cls.normalize_model_name(model_name)
        pricing = cls.MODEL_PRICING.get(model, cls.MODEL_PRICING["gpt-4o-mini"])
        return round(pricing["output"] * output_tokens, 6)

    @classmethod
    def calculate_input_cost_cents(cls, model_name: str, input_tokens: int) -> int:
        return int(round(cls.calculate_input_cost(model_name, input_tokens) * 100))

    @classmethod
    def calculate_output_cost_cents(cls, model_name: str, output_tokens: int) -> int:
        return int(round(cls.calculate_output_cost(model_name, output_tokens) * 100))

    @classmethod
    def calculate_total_cost_cents(cls, model_name: str, input_tokens: int, output_tokens: int) -> int:
        return cls.calculate_input_cost_cents(model_name, input_tokens) + cls.calculate_output_cost_cents(model_name, output_tokens)
