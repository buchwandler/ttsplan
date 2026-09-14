from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .model import TTSPlan


def to_dict(plan: TTSPlan) -> dict[str, Any]:
    return plan.to_dict()


def from_dict(data: Mapping[str, Any]) -> TTSPlan:
    return TTSPlan.from_dict(data)


def to_json(plan: TTSPlan, *, indent: int | None = 2) -> str:
    return plan.to_json(indent=indent)


def from_json(value: str) -> TTSPlan:
    return TTSPlan.from_json(value)
