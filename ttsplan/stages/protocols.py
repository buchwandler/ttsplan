from __future__ import annotations

from typing import Protocol

from ..config import PlannerConfig
from ..model import AnnotationSpan, BoundaryEvent
from ..parsers import ParsedDocument


class DocumentParser(Protocol):
    def parse(self, text: str, config: PlannerConfig) -> ParsedDocument: ...


class TextPreparer(Protocol):
    def prepare(
        self,
        text: str,
        language: str,
        runs: tuple[object, ...],
        annotations: tuple[AnnotationSpan, ...] = (),
        boundaries: tuple[BoundaryEvent, ...] = (),
    ) -> object: ...


__all__ = ["DocumentParser", "TextPreparer"]
