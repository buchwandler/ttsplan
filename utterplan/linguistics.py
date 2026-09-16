from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import LinguisticsConfig
from .language import LanguageRun
from .model import TokenAnnotation
from .spacy_models import resolve_spacy_model


@dataclass(frozen=True, slots=True)
class RunAnalysis:
    """Request-local linguistic state. Never serialize this object."""

    language: str
    start: int
    end: int
    tokens: tuple[TokenAnnotation, ...]
    provider_doc: object | None = None
    model_name: str | None = None


@dataclass(frozen=True, slots=True)
class LinguisticAnalysis:
    language: str
    text: str
    tokens: tuple[TokenAnnotation, ...]
    model_name: str | None = None
    provider_doc: object | None = None


class LinguisticResourcePool:
    """Cache local spaCy pipelines without downloading a model."""

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

    def _select_model(self, language: str, config: LinguisticsConfig) -> str | None:
        if config.spacy_model:
            return config.spacy_model
        if config.spacy_model_size:
            return resolve_spacy_model(language, config.spacy_model_size)
        if config.use_spacy is False:
            return None
        if config.use_spacy is not True:
            return None
        try:
            import spacy

            installed = set(spacy.util.get_installed_models())
        except ImportError:
            return None
        base = language.split("-", 1)[0].lower()
        families = (f"{base}_core_web_", f"{base}_core_news_")
        for suffix in ("trf", "lg", "md", "sm"):
            for family in families:
                candidate = family + suffix
                if candidate in installed:
                    return candidate
        return None

    def analyze(self, text: str, run: LanguageRun, config: LinguisticsConfig) -> LinguisticAnalysis:
        model = self._select_model(run.language, config)
        use_spacy = config.use_spacy if config.use_spacy is not None else model is not None
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
                    doc,
                )
            if config.require_spacy:
                raise RuntimeError("spaCy is required but no local model is available")
        return LinguisticAnalysis(
            run.language, text, _fallback_tokens(text, run.language), None, None
        )


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


def analyze_run_analyses(
    text: str,
    runs: tuple[LanguageRun, ...],
    config: LinguisticsConfig,
    pool: LinguisticResourcePool,
) -> tuple[RunAnalysis, ...]:
    analyses: list[RunAnalysis] = []
    for run in runs:
        local = text[run.spoken_start : run.spoken_end]
        analysis = pool.analyze(local, run, config)
        tokens = tuple(
            TokenAnnotation(
                token.spoken_start + run.spoken_start,
                token.spoken_end + run.spoken_start,
                token.text,
                token.pos,
                token.tag,
                token.lemma,
                token.language,
                f"token-{sum(len(item.tokens) for item in analyses) + i}",
            )
            for i, token in enumerate(analysis.tokens)
        )
        analyses.append(
            RunAnalysis(
                run.language,
                run.spoken_start,
                run.spoken_end,
                tokens,
                analysis.provider_doc,
                analysis.model_name,
            )
        )
    return tuple(analyses)


def analyze_runs(
    text: str,
    runs: tuple[LanguageRun, ...],
    config: LinguisticsConfig,
    pool: LinguisticResourcePool,
) -> tuple[TokenAnnotation, ...]:
    return tuple(
        token
        for analysis in analyze_run_analyses(text, runs, config, pool)
        for token in analysis.tokens
    )
