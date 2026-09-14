from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from .exceptions import TextPreparationError
from .language import LanguageRun
from .model import AnnotationSpan, BoundaryEvent, TextPreparationInfo


@dataclass(frozen=True, slots=True)
class PreparedText:
    spoken_text: str
    info: TextPreparationInfo
    annotations: tuple[AnnotationSpan, ...]
    boundaries: tuple[BoundaryEvent, ...]


class SpokenformTextPreparer:
    def prepare(
        self,
        text: str,
        language: str,
        runs: tuple[LanguageRun, ...],
        annotations: tuple[AnnotationSpan, ...] = (),
        boundaries: tuple[BoundaryEvent, ...] = (),
    ) -> PreparedText:
        try:
            import spokenform

            prepared = spokenform.prepare(
                text,
                language=language,
                use_spacy=False,
                strip_outer_whitespace=False,
                preserve_run_boundaries=True,
            )
            spoken = str(prepared.spoken_text)
            replacements = tuple(
                _replacement_dict(item) for item in getattr(prepared, "source_replacements", ())
            )
            offset_map = _plain_offset_map(getattr(prepared, "offset_map", None))
            backend = "spokenform"
            try:
                ver = version("spokenform")
            except PackageNotFoundError:
                ver = None
        except (ImportError, ValueError, TypeError) as exc:
            raise TextPreparationError(str(exc)) from exc
        mapped_annotations = tuple(
            _map_annotation(annotation, text, spoken) for annotation in annotations
        )
        mapped_boundaries = tuple(
            _map_boundary(boundary, len(text), len(spoken)) for boundary in boundaries
        )
        info = TextPreparationInfo(
            backend,
            ver,
            text,
            spoken,
            tuple(run.language for run in runs),
            replacements,
            offset_map,
            tuple(getattr(prepared, "warnings", ())),
        )
        return PreparedText(spoken, info, mapped_annotations, mapped_boundaries)


class IdentityTextPreparer:
    def prepare(
        self,
        text: str,
        language: str,
        runs: tuple[LanguageRun, ...],
        annotations: tuple[AnnotationSpan, ...] = (),
        boundaries: tuple[BoundaryEvent, ...] = (),
    ) -> PreparedText:
        info = TextPreparationInfo(
            "identity", None, text, text, tuple(run.language for run in runs)
        )
        return PreparedText(text, info, annotations, boundaries)


def _replacement_dict(item: Any) -> dict[str, Any]:
    return {
        key: getattr(item, key)
        for key in (
            "source_start",
            "source_end",
            "output_start",
            "output_end",
            "source",
            "replacement",
            "kind",
            "rule",
            "language",
        )
        if hasattr(item, key)
    }


def _plain_offset_map(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "source_length": getattr(value, "source_length", 0),
        "output_length": getattr(value, "output_length", 0),
        "edits": [_replacement_dict(item) for item in getattr(value, "edits", ())],
    }


def _map_position(position: int, source_length: int, output_length: int) -> int:
    return (
        min(output_length, max(0, position))
        if source_length == output_length
        else round(position * output_length / max(1, source_length))
    )


def _map_annotation(annotation: AnnotationSpan, source: str, output: str) -> AnnotationSpan:
    start = _map_position(annotation.structural_start, len(source), len(output))
    end = _map_position(annotation.structural_end, len(source), len(output))
    return AnnotationSpan(start, max(start, end), annotation.attrs, annotation.kind, annotation.id)


def _map_boundary(boundary: BoundaryEvent, source_length: int, output_length: int) -> BoundaryEvent:
    return BoundaryEvent(
        boundary.id,
        _map_position(boundary.position, source_length, output_length),
        boundary.kind,
        boundary.seconds,
        boundary.origin,
        boundary.strength,
        boundary.attrs,
    )
