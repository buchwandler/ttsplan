from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from .config import PlannerConfig
from .directives import resolve_directives
from .exceptions import PlanningError
from .language import build_language_runs, spans_from_annotations
from .linguistics import LinguisticResourcePool, analyze_run_analyses
from .model import (
    AnnotationSpan,
    BoundaryEvent,
    Diagnostic,
    Marker,
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
        parsed = self._parse(text, config)
        source_runs = build_language_runs(
            parsed.structural_text,
            spans_from_annotations(parsed.annotations),
            config.language,
            dict(config.language_aliases),
        )
        # Pass A is request-local state used by preparation. It is deliberately not
        # retained in the public plan.
        pass_a = analyze_run_analyses(
            parsed.structural_text, source_runs, config.linguistics, self._resources
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
            analyses=pass_a,
        )
        spoken = prepared.spoken_text
        runs = build_language_runs(
            spoken,
            spans_from_annotations(prepared.annotations),
            config.language,
            dict(config.language_aliases),
        )
        # Pass B is performed on the prepared language runs. Provider documents
        # and the Pass A values are released after this lightweight extraction.
        pass_b = analyze_run_analyses(
            spoken, runs, config.linguistics, self._resources
        )
        tokens = tuple(token for analysis in pass_b for token in analysis.tokens)
        boundaries = list(prepared.boundaries)
        boundaries.extend(
            _linguistic_boundaries(spoken, runs, config, start_id=len(boundaries))
        )
        segments = _segment(spoken, runs, prepared.annotations, boundaries, config, pass_b)
        boundaries.extend(_derived_boundaries(segments, boundaries, config))
        segments = _attach_membership(segments, tokens, prepared.annotations)
        segments = [resolve_directives(segment, prepared.annotations) for segment in segments]
        segments = resolve_pauses(segments, boundaries, config.pauses)
        markers = tuple(
            _map_marker(marker, prepared.info.offset_map, len(parsed.structural_text), len(spoken))
            for marker in parsed.markers
        )
        segment_tuple = tuple(segments)
        units = make_units(segment_tuple, markers, unit or config.unit)
        metadata = dict(parsed.metadata)
        metadata["planning"] = {
            "linguistic_passes": 2,
            "engine_independent": True,
            "pass_a_tokens": len(pass_a),
        }
        diagnostics: tuple[Diagnostic, ...] = ()
        if config.diagnostics:
            diagnostics = (
                Diagnostic(
                    "planning.complete",
                    "Plan compiled without renderer or audio processing",
                ),
            )
        plan = TTSPlan(
            source=PlanSource(parsed.source_text and config.document_format or "plain", text),
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

    def _parse(self, text: str, config: PlannerConfig) -> Any:
        if config.document_format == "plain":
            return PlainDocumentParser().parse(text, config)
        if config.document_format == "ssmd":
            return SSMDDocumentParser().parse(text, config)
        raise PlanningError(f"unsupported document format {config.document_format!r}")

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
    analyses: tuple[Any, ...] = (),
 ) -> list[PlanSegment]:
    if not text:
        return []
    result: list[PlanSegment] = []
    for run_index, run in enumerate(runs):
        local_text = text[run.spoken_start : run.spoken_end]
        analysis = analyses[run_index] if run_index < len(analyses) else None
        sentence_items = _split_run(local_text, run.language, config, analysis)
        for item in sentence_items:
            local_start = int(getattr(item, "char_start", 0))
            local_end = int(getattr(item, "char_end", len(local_text)))
            start = run.spoken_start + local_start
            end = run.spoken_start + local_end
            if end <= start or not text[start:end].strip():
                continue
            paragraph = int(getattr(item, "paragraph_idx", 0) or 0)
            sentence = int(getattr(item, "sentence_idx", 0) or 0)
            clause = int(getattr(item, "clause_idx", 0) or 0)
            cuts = {start, end}
            cuts.update(
                boundary.position for boundary in boundaries if start < boundary.position < end
            )
            cuts.update(
                point
                for annotation in annotations
                for point in (annotation.spoken_start, annotation.spoken_end)
                if point is not None and start < point < end and _semantic_annotation(annotation)
            )
            ordered = sorted(cuts)
            for part_start, part_end in zip(ordered, ordered[1:], strict=False):
                if part_end <= part_start or not text[part_start:part_end].strip():
                    continue
                result.append(
                    PlanSegment(
                        id=f"seg-{len(result):06d}",
                        text=text[part_start:part_end],
                        spoken_start=part_start,
                        spoken_end=part_end,
                        language=run.language,
                        paragraph=paragraph,
                        sentence=sentence,
                        clause=clause,
                        structural_start=None,
                        structural_end=None,
                    )
                )
    return result


def _split_run(
    text: str, language: str, config: PlannerConfig, analysis: Any | None = None
 ) -> list[Any]:
    try:
        import phrasplit

        kwargs: dict[str, Any] = {
            "mode": "sentence",
            "use_spacy": False,
            "language": language,
        }
        if analysis is not None and analysis.provider_doc is not None:
            kwargs["nlp"] = analysis.provider_doc
        items = phrasplit.split_with_offsets(text, **kwargs)
    except (ImportError, OSError, TypeError, ValueError):
        return [_FallbackSplit(0, len(text), 0, 0)] if text else []
    valid: list[Any] = []
    previous = 0
    for item in items:
        start = int(getattr(item, "char_start", -1))
        end = int(getattr(item, "char_end", -1))
        if not (0 <= start < end <= len(text)):
            continue
        if text[start:end] != str(getattr(item, "text", text[start:end])):
            continue
        if start < previous:
            continue
        valid.append(item)
        previous = end
    if not valid and text:
        return [_FallbackSplit(0, len(text), 0, 0, text)]
    if any(text[left.char_end:right.char_start].strip() for left, right in zip(valid, valid[1:], strict=False)):
        return [_FallbackSplit(0, len(text), 0, 0, text)]
    return _repair_quote_boundaries(valid, text)
def _repair_quote_boundaries(items: list[Any], text: str) -> list[Any]:
    repaired: list[Any] = []
    closing = "\\\"'”’)]}"
    for item in items:
        current = _FallbackSplit(
            int(item.char_start),
            int(item.char_end),
            int(getattr(item, "paragraph_idx", 0) or 0),
            int(getattr(item, "sentence_idx", 0) or 0),
            text[int(item.char_start) : int(item.char_end)],
        )
        if repaired and repaired[-1].text.rstrip().endswith((".", "!", "?")) and current.text.lstrip().startswith(tuple(closing)):
            previous = repaired[-1]
            previous.char_end = current.char_end
            previous.text = text[previous.char_start : previous.char_end]
        else:
            repaired.append(current)
    return repaired




class _FallbackSplit:
    def __init__(
        self,
        char_start: int,
        char_end: int,
        paragraph_idx: int,
        sentence_idx: int,
        text: str = "",
    ) -> None:
        self.char_start = char_start
        self.char_end = char_end
        self.paragraph_idx = paragraph_idx
        self.sentence_idx = sentence_idx
        self.clause_idx = 0
        self.text = text


def _linguistic_boundaries(
    text: str, runs: tuple[Any, ...], config: PlannerConfig, *, start_id: int = 0
 ) -> list[BoundaryEvent]:
    try:
        import phrasplit
    except ImportError:
        return []
    result: list[BoundaryEvent] = []
    for run in runs:
        local = text[run.spoken_start : run.spoken_end]
        try:
            clause_items = phrasplit.detect_clause_boundaries(
                local, language=run.language, use_spacy=False
            )
        except (OSError, TypeError, ValueError):
            clause_items = []
        for item in clause_items:
            kind = str(getattr(item, "kind", ""))
            if "parenthetical" in kind:
                event_kind = "parenthetical"
            elif "clause" in kind or "comma" in kind:
                event_kind = "clausal_comma"
            else:
                continue
            result.append(
                BoundaryEvent(
                    id=f"boundary-{start_id + len(result):06d}",
                    position=run.spoken_start + int(getattr(item, "char_start", 0)),
                    kind=event_kind,
                    origin="phrasplit",
                    strength="weak",
                    attrs={"detected_kind": kind, "automatic": True},
                )
            )
        try:
            parenthetical_items = phrasplit.detect_parenthetical_boundaries(
                local, language=run.language
            )
        except (AttributeError, OSError, TypeError, ValueError):
            parenthetical_items = []
        for item in parenthetical_items:
            result.append(
                BoundaryEvent(
                    id=f"boundary-{start_id + len(result):06d}",
                    position=run.spoken_start + int(getattr(item, "char_start", 0)),
                    kind="parenthetical",
                    origin="phrasplit",
                    strength="weak",
                    attrs={
                        "detected_kind": str(getattr(item, "kind", "parenthetical")),
                        "automatic": True,
                    },
                )
            )
    return result


def _derived_boundaries(
    segments: list[PlanSegment], existing: list[BoundaryEvent], config: PlannerConfig
) -> list[BoundaryEvent]:
    result: list[BoundaryEvent] = []
    next_id = len(existing)
    for previous, current in zip(segments, segments[1:], strict=False):
        kind: str | None = None
        strength: str | None = None
        if previous.paragraph != current.paragraph:
            kind, strength = "paragraph", "paragraph"
        elif previous.sentence != current.sentence:
            kind, strength = "sentence", "sentence"
        elif (
            previous.language != current.language
            and config.pauses.mode == "auto"
            and _voice_changed(previous, current)
        ):
            kind, strength = "voice_change", "weak"
        if kind is None:
            continue
        result.append(
            BoundaryEvent(
                id=f"boundary-{next_id:06d}",
                position=previous.spoken_end,
                kind=kind,
                origin="planner",
                strength=strength,
                attrs={"automatic": True},
            )
        )
        next_id += 1
    return result


def _voice_changed(previous: PlanSegment, current: PlanSegment) -> bool:
    left = previous.directives.voice.reference if previous.directives.voice else None
    right = current.directives.voice.reference if current.directives.voice else None
    return left != right


def _attach_membership(
    segments: list[PlanSegment], tokens: tuple[Any, ...], annotations: tuple[AnnotationSpan, ...]
) -> list[PlanSegment]:
    output: list[PlanSegment] = []
    for segment in segments:
        token_indices = tuple(
            index
            for index, token in enumerate(tokens)
            if token.spoken_start < segment.spoken_end and token.spoken_end > segment.spoken_start
        )
        annotation_ids = tuple(
            annotation.id
            for annotation in annotations
            if annotation.spoken_start is not None
            and annotation.spoken_end is not None
            and annotation.spoken_start < segment.spoken_end
            and annotation.spoken_end > segment.spoken_start
        )
        output.append(replace(segment, token_indices=token_indices, annotation_ids=annotation_ids))
    return output


def _semantic_annotation(annotation: AnnotationSpan) -> bool:
    return any(
        key in annotation.attrs
        for key in (
            "lang", "language", "voice", "voice_name", "ph", "phonemes", "rate", "pitch",
            "volume", "emphasis", "level", "audio", "audio_src", "src", "speed",
        )
    )


def _map_marker(marker: Marker, offset_map: Any, source_length: int, output_length: int) -> Marker:
    if not offset_map:
        return marker
    source_position = marker.spoken_position
    left = offset_map.get("source_left")
    if isinstance(left, list) and 0 <= source_position < len(left):
        position = int(left[source_position])
    elif source_length == output_length:
        position = source_position
    else:
        position = min(output_length, round(source_position * output_length / max(1, source_length)))
    return replace(marker, spoken_position=position)
