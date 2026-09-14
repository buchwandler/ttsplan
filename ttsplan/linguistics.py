from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import LinguisticsConfig
from .language import LanguageRun
from .model import TokenAnnotation


@dataclass(frozen=True, slots=True)
class LinguisticAnalysis:
    language: str
    text: str
    tokens: tuple[TokenAnnotation, ...]
    model_name: str | None = None


class LinguisticResourcePool:
    """Cache local spaCy pipelines without ever downloading a model."""

    def __init__(self) -> None:
        self._pipelines: dict[str, Any] = {}

    def pipeline(self, model: str | None, *, require: bool = False) -> Any | None:
        if not model:
            return None
        if model in self._pipelines:
            return self._pipelines[model]
        try:
            import spacy

            pipeline = spacy.load(model)
        except (ImportError, OSError, ValueError) as exc:
            if require:
                raise RuntimeError(f"Requested spaCy model {model!r} is unavailable") from exc
            return None
        self._pipelines[model] = pipeline
        return pipeline

    def clear(self) -> None:
        self._pipelines.clear()

    def analyze(self, text: str, run: LanguageRun, config: LinguisticsConfig) -> LinguisticAnalysis:
        model = config.spacy_model
        if model is None and config.spacy_model_size:
            base = run.language.split("-", 1)[0]
            model = {
                "sm": f"{base}_core_web_sm",
                "md": f"{base}_core_web_md",
                "lg": f"{base}_core_web_lg",
                "trf": f"{base}_core_web_trf",
            }[config.spacy_model_size]
        use_spacy = config.use_spacy if config.use_spacy is not None else bool(model)
        if use_spacy:
            pipeline = self.pipeline(model, require=config.require_spacy)
            if pipeline is not None:
                doc = pipeline(text)
                return LinguisticAnalysis(
                    run.language,
                    text,
                    tuple(
                        TokenAnnotation(
                            int(token.idx),
                            int(token.idx + len(token.text)),
                            str(token.text),
                            getattr(token, "pos_", None) or None,
                            getattr(token, "tag_", None) or None,
                            getattr(token, "lemma_", None) or None,
                            run.language,
                            f"token-{i}",
                        )
                        for i, token in enumerate(doc)
                        if token.text
                    ),
                    model,
                )
            if config.require_spacy:
                raise RuntimeError("spaCy is required but no local model is available")
        return LinguisticAnalysis(run.language, text, _fallback_tokens(text, run.language), None)


def _fallback_tokens(text: str, language: str) -> tuple[TokenAnnotation, ...]:
    return tuple(
        TokenAnnotation(
            match.start(),
            match.end(),
            match.group(0),
            None,
            None,
            match.group(0).lower(),
            language,
            f"token-{i}",
        )
        for i, match in enumerate(re.finditer(r"\S+", text))
    )


def analyze_runs(
    text: str,
    runs: tuple[LanguageRun, ...],
    config: LinguisticsConfig,
    pool: LinguisticResourcePool,
) -> tuple[TokenAnnotation, ...]:
    output: list[TokenAnnotation] = []
    for run in runs:
        analysis = pool.analyze(text[run.spoken_start : run.spoken_end], run, config)
        for token in analysis.tokens:
            output.append(
                TokenAnnotation(
                    token.spoken_start + run.spoken_start,
                    token.spoken_end + run.spoken_start,
                    token.text,
                    token.pos,
                    token.tag,
                    token.lemma,
                    token.language,
                    f"token-{len(output)}",
                )
            )
    return tuple(output)
