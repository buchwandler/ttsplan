from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import UtterancePlan
from .schema_registry import schema as _schema
from .versioning import FORMAT, SCHEMA_VERSION

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "spec" / "utterplan.schema.json"
PACKAGE_SCHEMA_PATH = Path(__file__).resolve().parent / "utterplan.schema.json"


def validate_json(value: Any) -> UtterancePlan:
    return UtterancePlan.from_dict(value)


def validate_file(path: str | Path) -> UtterancePlan:
    return UtterancePlan.load(path)


def schema(version: int | None = None) -> dict[str, Any]:
    return _schema(version)


__all__ = [
    "FORMAT",
    "SCHEMA_VERSION",
    "SCHEMA_PATH",
    "PACKAGE_SCHEMA_PATH",
    "validate_json",
    "validate_file",
    "schema",
]
