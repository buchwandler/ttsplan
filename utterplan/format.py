from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import FORMAT, SCHEMA_VERSION, UtterancePlan

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "spec" / "utterplan.schema.json"
PACKAGE_SCHEMA_PATH = Path(__file__).resolve().parent / "utterplan.schema.json"


def validate_json(value: Any) -> UtterancePlan:
    return UtterancePlan.from_dict(value)


def validate_file(path: str | Path) -> UtterancePlan:
    return UtterancePlan.load(path)


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
