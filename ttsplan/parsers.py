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
                id=f"boundary-{index:06d}",
                position=match.start(),
                kind="paragraph",
                origin="plain",
                strength="paragraph",
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
                id=f"annotation-{i:06d}",
                kind=str(getattr(item, "kind", "annotation")),
                attrs={str(k): _plain_value(v) for k, v in item.attrs.items()},
                structural_start=int(item.char_start),
                structural_end=int(item.char_end),
            )
            for i, item in enumerate(parsed.annotations)
            if int(item.char_end) > int(item.char_start)
        )
        boundaries: list[BoundaryEvent] = []
        markers: list[Marker] = []
        warnings = tuple(str(x) for x in parsed.warnings)
        for event in parsed.events:
            attrs = {str(k): _plain_value(v) for k, v in event.attrs.items()}
            kind = str(event.kind)
            position = int(getattr(event, "pos", getattr(event, "position", 0)))
            event_anchor = str(getattr(event, "anchor", attrs.get("anchor", "after")))
            if kind == "mark":
                name = attrs.get("name") or attrs.get("marker") or "marker"
                markers.append(
                    Marker(f"marker-{len(markers):06d}", name, position, attrs)
                )
            elif kind == "break":
                seconds = _duration(attrs, config, parsed.header)
                boundaries.append(
                    BoundaryEvent(
                        id=f"boundary-{len(boundaries):06d}",
                        position=position,
                        kind="explicit",
                        seconds=seconds,
                        origin="ssmd",
                        strength=attrs.get("strength"),
                        attrs={
                            **attrs,
                            "anchor": event_anchor,
                            "pause_origin": _duration_origin(attrs, config, parsed.header),
                        },
                    )
                )
            elif kind == "paragraph":
                boundaries.append(
                    BoundaryEvent(
                        id=f"boundary-{len(boundaries):06d}",
                        position=position,
                        kind="paragraph",
                        seconds=_duration(attrs, config, parsed.header),
                        origin="ssmd",
                        strength=attrs.get("strength", "paragraph"),
                        attrs={
                            **attrs,
                            "anchor": event_anchor,
                            "pause_origin": _duration_origin(attrs, config, parsed.header),
                        },
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


def _plain_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _duration(
    attrs: dict[str, Any], config: PlannerConfig, header: dict[str, Any] | None = None
 ) -> float | None:
    value = attrs.get("time")
    if value is not None:
        if str(value).strip().lower() in {"none", "0", "0s", "0ms"}:
            return 0.0
        match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(ms|s)\s*", str(value), re.I)
        if match:
            return float(match.group(1)) / 1000 if match.group(2).lower() == "ms" else float(match.group(1))
    strength = str(attrs.get("strength", "")).lower()
    key = {"x-weak": "weak", "weak": "weak", "medium": "clause", "strong": "sentence", "x-strong": "paragraph"}.get(strength)
    defaults: dict[str, Any] = {}
    if config.ssmd.pause_defaults:
        defaults.update(config.ssmd.pause_defaults)
    if header and isinstance(header.get("pause_defaults"), dict):
        defaults.update(header["pause_defaults"])
    if key in defaults:
        return float(defaults[key])
    planner_defaults = {
        "weak": config.pauses.weak,
        "clause": config.pauses.clause,
        "sentence": config.pauses.sentence,
        "paragraph": config.pauses.paragraph,
    }
    return planner_defaults.get(key) if key else None

def _duration_origin(attrs: dict[str, Any], config: PlannerConfig, header: dict[str, Any]) -> str:
    if attrs.get("time") is not None:
        return "explicit"
    strength = str(attrs.get("strength", "")).lower()
    key = {"x-weak": "weak", "weak": "weak", "medium": "clause", "strong": "sentence", "x-strong": "paragraph"}.get(strength)
    header_defaults = header.get("pause_defaults")
    if isinstance(header_defaults, dict) and header_defaults.get(key) is not None:
        return "header_default"
    if config.ssmd.pause_defaults and key in config.ssmd.pause_defaults:
        return "config_default"
    return "planner_default" if key else "none"
