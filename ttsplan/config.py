from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class PauseConfig:
    mode: Literal["tts", "manual", "auto"] = "tts"
    weak: float = 0.15
    clause: float = 0.30
    sentence: float = 0.60
    paragraph: float = 1.00
    parenthetical: float = 0.15


@dataclass(frozen=True, slots=True)
class LinguisticsConfig:
    use_spacy: bool | None = None
    spacy_model: str | None = None
    spacy_model_size: Literal["sm", "md", "lg", "trf"] | None = None
    require_spacy: bool = False


@dataclass(frozen=True, slots=True)
class SSMDConfig:
    parse_header: bool = True
    strict_header: bool = True
    unknown_header: Literal["warn", "error", "ignore"] = "warn"
    pause_defaults: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class PlannerConfig:
    language: str
    document_format: Literal["plain", "ssmd"] = "ssmd"
    text_preparation: Literal["spokenform", "identity"] = "spokenform"
    unit: Literal["paragraph", "sentence"] = "paragraph"
    pauses: PauseConfig = field(default_factory=PauseConfig)
    linguistics: LinguisticsConfig = field(default_factory=LinguisticsConfig)
    ssmd: SSMDConfig = field(default_factory=SSMDConfig)
    overlap_mode: Literal["snap", "strict"] = "snap"
    language_aliases: Mapping[str, str] = field(default_factory=dict)
    diagnostics: bool = True
