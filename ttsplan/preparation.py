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
        analyses: tuple[Any, ...] = (),
    ) -> PreparedText:
        try:
            import spokenform

            prepared_runs: list[Any] = []
            active_runs = runs or (LanguageRun("lang-0", 0, len(text), language),)
            for run_index, run in enumerate(active_runs):
                local_text = text[run.spoken_start : run.spoken_end]
                protected = [
                    (
                        annotation.structural_start - run.spoken_start,
                        annotation.structural_end - run.spoken_start,
                    )
                    for annotation in annotations
                    if annotation.structural_start >= run.spoken_start
                    and annotation.structural_end <= run.spoken_end
                    and (annotation.attrs.get("ph") or annotation.attrs.get("phonemes"))
                ]
                kwargs: dict[str, Any] = {
                    "language": run.language,
                    "use_spacy": False,
                    "strip_outer_whitespace": False,
                    "preserve_run_boundaries": True,
                    "protected_spans": protected,
                }
                if run_index < len(analyses) and analyses[run_index].provider_doc is not None:
                    kwargs["nlp"] = analyses[run_index].provider_doc
                prepared_runs.append(spokenform.prepare(local_text, **kwargs))
            spoken = "".join(str(item.spoken_text) for item in prepared_runs)
            offset = _compose_offsets(text, prepared_runs)
            replacements: list[dict[str, Any]] = []
            warnings: list[str] = []
            output_offset = 0
            for run, item in zip(
                runs or (LanguageRun("lang-0", 0, len(text), language),),
                prepared_runs,
                strict=False,
            ):
                for replacement in getattr(item, "source_replacements", ()):
                    value = _replacement_dict(replacement)
                    value["source_start"] = int(value.get("source_start", 0)) + run.spoken_start
                    value["source_end"] = int(value.get("source_end", 0)) + run.spoken_start
                    value["output_start"] = int(value.get("output_start", 0)) + output_offset
                    value["output_end"] = int(value.get("output_end", 0)) + output_offset
                    replacements.append(value)
                warnings.extend(str(value) for value in getattr(item, "warnings", ()))
                output_offset += len(str(item.spoken_text))
            try:
                ver = version("spokenform")
            except PackageNotFoundError:
                ver = None
        except (ImportError, ValueError, TypeError) as exc:
            raise TextPreparationError(str(exc)) from exc
        mapped_annotations = tuple(
            _map_annotation(annotation, offset) for annotation in annotations
        )
        mapped_boundaries = tuple(_map_boundary(boundary, offset) for boundary in boundaries)
        info = TextPreparationInfo(
            "spokenform",
            ver,
            text,
            spoken,
            tuple(run.language for run in runs),
            tuple(replacements),
            offset.to_dict(),
            tuple(warnings),
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
        analyses: tuple[Any, ...] = (),
    ) -> PreparedText:
        offset = _IdentityOffsetMap(len(text))
        info = TextPreparationInfo(
            "identity",
            None,
            text,
            text,
            tuple(run.language for run in runs),
            (),
            offset.to_dict(),
            (),
        )
        return PreparedText(
            text,
            info,
            tuple(_map_annotation(annotation, offset) for annotation in annotations),
            tuple(_map_boundary(boundary, offset) for boundary in boundaries),
        )


class _IdentityOffsetMap:
    def __init__(self, length: int) -> None:
        self.source_length = length
        self.output_length = length

    def map_source_span(self, start: int, end: int) -> tuple[int, int]:
        return start, end

    def to_dict(self) -> dict[str, Any]:
        values = list(range(self.source_length + 1))
        return {
            "source_length": self.source_length,
            "output_length": self.output_length,
            "source_left": values,
            "source_right": values,
            "output_left": values,
            "output_right": values,
            "edits": [],
        }


class _CompositeOffsetMap:
    def __init__(
        self,
        source_length: int,
        output_length: int,
        source_left: list[int],
        source_right: list[int],
        output_left: list[int],
        output_right: list[int],
        edits: list[dict[str, Any]],
    ) -> None:
        self.source_length = source_length
        self.output_length = output_length
        self.source_left = source_left
        self.source_right = source_right
        self.output_left = output_left
        self.output_right = output_right
        self.edits = edits

    def map_source_span(self, start: int, end: int) -> tuple[int, int]:
        start = max(0, min(self.source_length, start))
        end = max(start, min(self.source_length, end))
        return self.source_left[start], self.source_right[end]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_length": self.source_length,
            "output_length": self.output_length,
            "source_left": self.source_left,
            "source_right": self.source_right,
            "output_left": self.output_left,
            "output_right": self.output_right,
            "edits": self.edits,
        }


def _compose_offsets(text: str, prepared_runs: list[Any]) -> _CompositeOffsetMap:
    if not prepared_runs:
        return _IdentityOffsetMap(len(text))  # type: ignore[return-value]
    source_left: list[int] = []
    source_right: list[int] = []
    output_left: list[int] = []
    output_right: list[int] = []
    edits: list[dict[str, Any]] = []
    source_offset = output_offset = 0
    for item in prepared_runs:
        offset = getattr(item, "offset_map", None)
        if offset is None:
            raise TextPreparationError("spokenform did not provide an offset map")
        local_left = list(offset.source_left)
        local_right = list(offset.source_right)
        local_output_left = list(offset.output_left)
        local_output_right = list(offset.output_right)
        if not source_left:
            source_left.extend(value + output_offset for value in local_left)
            source_right.extend(value + output_offset for value in local_right)
        else:
            source_left.extend(value + output_offset for value in local_left[1:])
            source_right.extend(value + output_offset for value in local_right[1:])
        output_left.extend(value + source_offset for value in local_output_left)
        output_right.extend(value + source_offset for value in local_output_right)
        edits.extend(_replacement_dict(edit) for edit in getattr(offset, "edits", ()))
        source_offset += int(offset.source_length)
        output_offset += int(offset.output_length)
    return _CompositeOffsetMap(
        source_offset, output_offset, source_left, source_right, output_left, output_right, edits
    )


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


def _map_annotation(annotation: AnnotationSpan, offset_map: Any) -> AnnotationSpan:
    spoken_start, spoken_end = offset_map.map_source_span(
        annotation.structural_start, annotation.structural_end
    )
    return AnnotationSpan(
        annotation.id,
        annotation.kind,
        annotation.attrs,
        annotation.structural_start,
        annotation.structural_end,
        spoken_start,
        max(spoken_start, spoken_end),
    )


def _map_boundary(boundary: BoundaryEvent, offset_map: Any) -> BoundaryEvent:
    position, _ = offset_map.map_source_span(boundary.position, boundary.position)
    return BoundaryEvent(
        boundary.id,
        position,
        boundary.kind,
        boundary.seconds,
        boundary.origin,
        boundary.strength,
        boundary.attrs,
    )
