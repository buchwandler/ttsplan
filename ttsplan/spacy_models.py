from __future__ import annotations

from typing import Literal

SpacyModelSize = Literal["sm", "md", "lg", "trf"]


def resolve_spacy_model(language: str, size: SpacyModelSize = "sm") -> str:
    base = language.lower().replace("_", "-").split("-", 1)[0]
    return f"{base}_core_web_{size}"


__all__ = ["SpacyModelSize", "resolve_spacy_model"]
