from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import FORMAT, SCHEMA_VERSION, TTSPlan

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "spec" / "ttsplan.schema.json"
PACKAGE_SCHEMA_PATH = Path(__file__).resolve().parent / "ttsplan.schema.json"


def validate_json(value: Any) -> TTSPlan:
    return TTSPlan.from_dict(value)


def validate_file(path: str | Path) -> TTSPlan:
    return TTSPlan.load(path)


def schema() -> dict[str, Any]:
    path = SCHEMA_PATH if SCHEMA_PATH.exists() else PACKAGE_SCHEMA_PATH
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "FORMAT",
    "SCHEMA_VERSION",
    "SCHEMA_PATH",
    "PACKAGE_SCHEMA_PATH",
    "validate_json",
    "validate_file",
    "schema",
]
