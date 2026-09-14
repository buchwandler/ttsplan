from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .config import PlannerConfig
from .model import AnnotationSpan, BoundaryEvent, Marker


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    source_text: str
    structural_text: str
    annotations: tuple[AnnotationSpan, ...] = ()
    boundaries: tuple[BoundaryEvent, ...] = ()
    markers: tuple[Marker, ...] = ()
    header: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


class PlainDocumentParser:
    def parse(self, text: str, config: PlannerConfig) -> ParsedDocument:
        boundaries = tuple(
            BoundaryEvent(
                f"boundary-{index}", match.start(), "paragraph", None, "plain", "paragraph"
            )
            for index, match in enumerate(re.finditer(r"\n\s*\n", text))
        )
        return ParsedDocument(text, text, boundaries=boundaries)


class SSMDDocumentParser:
    def parse(self, text: str, config: PlannerConfig) -> ParsedDocument:
        try:
            import ssmd

            parsed = ssmd.parse_structure(
                text, default_lang=config.language, parse_yaml_header=config.ssmd.parse_header
            )
        except ImportError as exc:
            raise RuntimeError("SSMD input requires the ssmd package") from exc
        structural = str(parsed.clean_text)
        annotations = tuple(
            AnnotationSpan(
                int(item.char_start),
                int(item.char_end),
                {str(k): str(v) for k, v in item.attrs.items()},
                str(getattr(item, "kind", "annotation")),
                f"annotation-{i}",
            )
            for i, item in enumerate(parsed.annotations)
            if int(item.char_end) > int(item.char_start)
        )
        boundaries: list[BoundaryEvent] = []
        markers: list[Marker] = []
        warnings = tuple(str(x) for x in parsed.warnings)
        for event in parsed.events:
            attrs = {str(k): str(v) for k, v in event.attrs.items()}
            kind = str(event.kind)
            if kind == "mark":
                name = attrs.get("name") or attrs.get("marker") or "marker"
                markers.append(Marker(f"marker-{len(markers)}", name, int(event.pos), attrs))
            elif kind in {"break", "paragraph"}:
                seconds = _duration(attrs, config)
                semantic_kind = (
                    "explicit" if kind == "break" and seconds is not None else "paragraph"
                )
                boundaries.append(
                    BoundaryEvent(
                        f"boundary-{len(boundaries)}",
                        int(event.pos),
                        semantic_kind,
                        seconds,
                        "ssmd",
                        attrs.get("strength"),
                        attrs,
                    )
                )
        metadata = {"header": dict(parsed.header)}
        if parsed.header.get("voice_bindings") is not None:
            metadata["voice_bindings"] = parsed.header["voice_bindings"]
        return ParsedDocument(
            text,
            structural,
            annotations,
            tuple(boundaries),
            tuple(markers),
            dict(parsed.header),
            metadata,
            warnings,
        )


def _duration(attrs: dict[str, str], config: PlannerConfig) -> float | None:
    value = attrs.get("time")
    if value:
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(ms|s)\s*", value, re.I)
        if match:
            return (
                float(match.group(1)) / 1000
                if match.group(2).lower() == "ms"
                else float(match.group(1))
            )
    strength = attrs.get("strength", "").lower()
    defaults = {
        "x-weak": config.pauses.weak,
        "weak": config.pauses.weak,
        "medium": config.pauses.clause,
        "strong": config.pauses.sentence,
        "x-strong": config.pauses.paragraph,
    }
    return defaults.get(strength, 0.0) or None
