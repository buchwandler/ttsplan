from __future__ import annotations

from typing import Literal

SpacyModelSize = Literal["sm", "md", "lg", "trf"]


def normalize_spacy_language(language: str | None) -> str:
    value = (language or "en").strip().lower().replace("_", "-")
    return value.split("-", 1)[0] or "en"


def resolve_spacy_model(language: str, size: SpacyModelSize = "sm") -> str:
    if size not in {"sm", "md", "lg", "trf"}:
        raise ValueError("spacy model size must be one of sm, md, lg, trf")
    base = normalize_spacy_language(language)
    family = "web" if base in {"en", "zh"} else "news"
    return f"{base}_core_{family}_{size}"


__all__ = ["SpacyModelSize", "normalize_spacy_language", "resolve_spacy_model"]
