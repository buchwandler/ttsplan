from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from .config import PlannerConfig
from .directives import resolve_directives
from .exceptions import PlanningError
from .language import build_language_runs, spans_from_annotations
from .linguistics import LinguisticResourcePool, analyze_runs
from .model import (
    AnnotationSpan,
    BoundaryEvent,
    Diagnostic,
    PlanSegment,
    PlanSource,
    PlanTexts,
    TTSPlan,
)
from .parsers import PlainDocumentParser, SSMDDocumentParser
from .pauses import resolve_pauses
from .preparation import IdentityTextPreparer, SpokenformTextPreparer
from .units import make_units


class TTSPlanner:
    def __init__(self, config: PlannerConfig) -> None:
        self.config = config
        self._resources = LinguisticResourcePool()

    def plan(self, text: str, *, unit: str | None = None) -> TTSPlan:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        config = self.config
        format_name = config.document_format
        if format_name == "plain":
            parsed = PlainDocumentParser().parse(text, config)
        elif format_name == "ssmd":
            parsed = SSMDDocumentParser().parse(text, config)
        else:
            raise PlanningError(f"unsupported document format {format_name!r}")
        source_runs = build_language_runs(
            parsed.structural_text,
            spans_from_annotations(parsed.annotations),
            config.language,
            dict(config.language_aliases),
        )
        preparer = (
            IdentityTextPreparer()
            if config.text_preparation == "identity"
            else SpokenformTextPreparer()
        )
        prepared = preparer.prepare(
            parsed.structural_text,
            config.language,
            source_runs,
            parsed.annotations,
            parsed.boundaries,
        )
        spoken = prepared.spoken_text
        runs = build_language_runs(
            spoken,
            spans_from_annotations(prepared.annotations),
            config.language,
            dict(config.language_aliases),
        )
        # Pass A and Pass B deliberately use the same cache and produce only lightweight values.
        _pass_a = analyze_runs(
            parsed.structural_text, source_runs, config.linguistics, self._resources
        )
        tokens = analyze_runs(spoken, runs, config.linguistics, self._resources)
        segments = _segment(spoken, runs, prepared.annotations, list(prepared.boundaries), config)
        boundaries = list(prepared.boundaries)
        boundaries.extend(_derived_boundaries(segments, config))
        segments = [resolve_directives(segment, prepared.annotations) for segment in segments]
        segments = resolve_pauses(segments, boundaries, config.pauses)
        markers = tuple(
            _map_marker(marker, len(parsed.structural_text), len(spoken))
            for marker in parsed.markers
        )
        segment_tuple = tuple(segments)
        units = make_units(segment_tuple, markers, unit or config.unit)
        metadata = dict(parsed.metadata)
        metadata["planning"] = {"linguistic_passes": 2, "engine_independent": True}
        diagnostics: tuple[Diagnostic, ...] = ()
        if config.diagnostics:
            diagnostics = (
                Diagnostic(
                    "planning.complete", "Plan compiled without renderer or audio processing"
                ),
            )
        plan = TTSPlan(
            source=PlanSource(format_name, text),
            config=_config_dict(config),
            texts=PlanTexts(parsed.structural_text, spoken),
            preparation=prepared.info,
            languages=runs,
            annotations=prepared.annotations,
            boundaries=tuple(boundaries),
            tokens=tokens,
            segments=segment_tuple,
            units=units,
            markers=markers,
            document_metadata=metadata,
            warnings=tuple(parsed.warnings) + prepared.info.warnings,
            diagnostics=diagnostics,
        ).with_identity()
        plan.validate()
        return plan

    def close(self) -> None:
        self._resources.clear()


def _config_dict(config: PlannerConfig) -> dict[str, Any]:
    result = asdict(config)
    result["language_aliases"] = dict(config.language_aliases)
    return result


def _segment(
    text: str,
    runs: tuple[Any, ...],
    annotations: tuple[AnnotationSpan, ...],
    boundaries: list[BoundaryEvent],
    config: PlannerConfig,
) -> list[PlanSegment]:
    if not text:
        return []
    try:
        import phrasplit

        sentence_items = phrasplit.split_with_offsets(
            text, mode="sentence", use_spacy=False, language=config.language
        )
    except (ImportError, OSError, TypeError, ValueError):
        sentence_items = []
    sentence_ranges = [
        (
            int(item.char_start),
            int(item.char_end),
            int(getattr(item, "paragraph_idx", 0) or 0),
            int(getattr(item, "sentence_idx", 0) or 0),
        )
        for item in sentence_items
        if getattr(item, "char_end", 0) > getattr(item, "char_start", 0)
    ]
    if not sentence_ranges:
        sentence_ranges = [(0, len(text), text[:].count("\n\n"), 0)]
    result: list[PlanSegment] = []
    segment_index = 0
    for sentence_start, sentence_end, paragraph, sentence in sentence_ranges:
        cuts = {sentence_start, sentence_end}
        cuts.update(
            run.spoken_start for run in runs if sentence_start < run.spoken_start < sentence_end
        )
        cuts.update(
            run.spoken_end for run in runs if sentence_start < run.spoken_end < sentence_end
        )
        for boundary in boundaries:
            if sentence_start < boundary.position < sentence_end:
                cuts.add(boundary.position)
        for annotation in annotations:
            if (
                annotation.structural_start > sentence_start
                and annotation.structural_start < sentence_end
            ):
                cuts.add(annotation.structural_start)
            if (
                annotation.structural_end > sentence_start
                and annotation.structural_end < sentence_end
                and _semantic_annotation(annotation)
            ):
                cuts.add(annotation.structural_end)
        ordered = sorted(cuts)
        clause = 0
        for start, end in zip(ordered, ordered[1:], strict=False):
            if end <= start or not text[start:end].strip():
                continue
            language = next(
                (
                    run.language
                    for run in runs
                    if run.spoken_start <= start and end <= run.spoken_end
                ),
                config.language,
            )
            if (
                result
                and result[-1].sentence == sentence
                and result[-1].paragraph == paragraph
                and start > result[-1].spoken_end
            ):
                pass
            result.append(
                PlanSegment(
                    f"seg-{segment_index:06d}",
                    text[start:end],
                    start,
                    end,
                    language,
                    paragraph,
                    sentence,
                    clause,
                    start,
                    end,
                )
            )
            segment_index += 1
            clause += 1
    return result


def _semantic_annotation(annotation: AnnotationSpan) -> bool:
    return any(
        key in annotation.attrs
        for key in (
            "lang",
            "language",
            "voice",
            "voice_name",
            "ph",
            "phonemes",
            "rate",
            "pitch",
            "volume",
            "emphasis",
            "level",
            "audio",
            "audio_src",
            "src",
        )
    )


def _derived_boundaries(segments: list[PlanSegment], config: PlannerConfig) -> list[BoundaryEvent]:
    result: list[BoundaryEvent] = []
    for previous, current in zip(segments, segments[1:], strict=False):
        if previous.paragraph != current.paragraph:
            result.append(
                BoundaryEvent(
                    f"boundary-{len(result):04d}",
                    previous.spoken_end,
                    "paragraph",
                    None,
                    "planner",
                    "paragraph",
                )
            )
        elif previous.sentence != current.sentence:
            result.append(
                BoundaryEvent(
                    f"boundary-{len(result):04d}",
                    previous.spoken_end,
                    "sentence",
                    None,
                    "planner",
                    "sentence",
                )
            )
        elif previous.clause != current.clause:
            result.append(
                BoundaryEvent(
                    f"boundary-{len(result):04d}",
                    previous.spoken_end,
                    "clausal_comma",
                    None,
                    "phrasplit",
                    "clause",
                )
            )
        if previous.language != current.language:
            result.append(
                BoundaryEvent(
                    f"boundary-{len(result):04d}",
                    previous.spoken_end,
                    "voice_change",
                    None,
                    "planner",
                    "weak",
                )
            )
    return result


def _map_marker(marker: Any, source_length: int, output_length: int) -> Any:
    if source_length == output_length:
        return marker
    position = round(marker.spoken_position * output_length / max(1, source_length))
    return replace(marker, spoken_position=position)
