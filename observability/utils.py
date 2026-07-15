from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import tiktoken


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_summary(text: str, max_length: int = 128) -> str:
    summary = text.strip()
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 1] + "…"


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    model_name = model.replace("openai/", "").replace("gpt-", "gpt-")
    try:
        enc = tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return max(1, len(text.split()))
    return len(enc.encode(text))


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def json_safe(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.loads(json.dumps(value, default=str))
    return value
