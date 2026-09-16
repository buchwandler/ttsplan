from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .model import UtterancePlan


def to_dict(plan: UtterancePlan) -> dict[str, Any]:
    return plan.to_dict()


def from_dict(data: Mapping[str, Any]) -> UtterancePlan:
    return UtterancePlan.from_dict(data)


def to_json(plan: UtterancePlan, *, indent: int | None = 2) -> str:
    return plan.to_json(indent=indent)


def from_json(value: str) -> UtterancePlan:
    return UtterancePlan.from_json(value)
