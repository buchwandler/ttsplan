from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .config import PlannerConfig, parse_duration
from .exceptions import ConfigurationError, PlanFormatError, PlanningError
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
        except ImportError as exc:
            raise PlanningError("SSMD input requires the ssmd package") from exc

        warnings: list[str] = []
        if config.ssmd.parse_header:
            self._validate_header(text, config, warnings)
        try:
            parsed = ssmd.parse_structure(
                text,
                default_lang=config.language,
                parse_yaml_header=config.ssmd.parse_header,
            )
        except (ImportError, OSError) as exc:
            raise PlanningError("SSMD parsing failed") from exc
        except (TypeError, ValueError) as exc:
            raise PlanFormatError(str(exc), code="header.invalid") from exc

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
        warnings.extend(str(x) for x in parsed.warnings)
        for event in parsed.events:
            attrs = {str(k): _plain_value(v) for k, v in event.attrs.items()}
            kind = str(event.kind)
            position = int(getattr(event, "pos", getattr(event, "position", 0)))
            event_anchor = str(getattr(event, "anchor", attrs.get("anchor", "after")))
            if kind == "mark":
                name = attrs.get("name") or attrs.get("marker") or "marker"
                markers.append(Marker(f"marker-{len(markers):06d}", name, position, attrs))
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
            tuple(warnings),
        )

    @staticmethod
    def _validate_header(text: str, config: PlannerConfig, warnings: list[str]) -> None:
        try:
            from ssmd.frontmatter import parse_front_matter

            front_matter = parse_front_matter(text)
        except (ImportError, OSError) as exc:
            raise PlanningError("SSMD header parser is unavailable") from exc
        except ValueError as exc:
            raise PlanFormatError(str(exc), code="header.yaml_invalid") from exc
        if not front_matter.present:
            return

        header = front_matter.data
        known = {"pause_defaults", "voice_bindings"}
        unknown = sorted(set(header) - known)
        if unknown:
            message = f"unknown SSMD header key(s): {', '.join(unknown)}"
            if config.ssmd.unknown_header == "error":
                raise PlanFormatError(message, code="header.unknown")
            if config.ssmd.unknown_header == "warn":
                warnings.append(message)

        pause_defaults = header.get("pause_defaults")
        if pause_defaults is None:
            return
        if not isinstance(pause_defaults, dict):
            _header_invalid(config, warnings, "pause_defaults must be a mapping")
            return
        allowed = {
            "enabled",
            "weak",
            "clause",
            "sentence",
            "paragraph",
            "parenthetical",
            "voice_change",
        }
        for key, value in pause_defaults.items():
            if key not in allowed:
                _header_invalid(config, warnings, f"unsupported pause_defaults key: {key}")
                continue
            try:
                if key == "enabled":
                    if not isinstance(value, bool):
                        raise ConfigurationError("enabled must be a boolean")
                else:
                    parse_duration(value, field_name=f"pause_defaults.{key}")
            except ConfigurationError as exc:
                _header_invalid(config, warnings, str(exc))


def _header_invalid(config: PlannerConfig, warnings: list[str], message: str) -> None:
    if config.ssmd.strict_header:
        raise PlanFormatError(message, code="header.invalid")
    warnings.append(message)


def _plain_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _duration(
    attrs: dict[str, Any], config: PlannerConfig, header: dict[str, Any] | None = None
) -> float | None:
    value = attrs.get("time")
    if value is not None:
        try:
            return parse_duration(value, field_name="break.time")
        except ConfigurationError as exc:
            raise PlanFormatError(str(exc), code="break.duration") from exc

    strength = str(attrs.get("strength", "")).lower()
    key = {
        "x-weak": "weak",
        "weak": "weak",
        "medium": "clause",
        "strong": "sentence",
        "x-strong": "paragraph",
    }.get(strength)
    defaults: dict[str, Any] = {
        "weak": config.pauses.weak,
        "clause": config.pauses.clause,
        "sentence": config.pauses.sentence,
        "paragraph": config.pauses.paragraph,
        "parenthetical": config.pauses.parenthetical,
        "voice_change": config.pauses.voice_change,
    }
    if header and isinstance(header.get("pause_defaults"), dict):
        for name, candidate in header["pause_defaults"].items():
            if name == "enabled":
                continue
            try:
                parse_duration(candidate, field_name=f"pause_defaults.{name}")
            except ConfigurationError:
                continue
            defaults[name] = candidate
    if config.ssmd.pause_defaults:
        defaults.update(config.ssmd.pause_defaults)
    if not _pause_enabled(config, header):
        return None
    if key in defaults:
        try:
            return parse_duration(defaults[key], field_name=f"pause_defaults.{key}")
        except ConfigurationError as exc:
            raise PlanFormatError(str(exc), code="pause.duration") from exc
    return None


def _pause_enabled(config: PlannerConfig, header: dict[str, Any] | None) -> bool:
    enabled = config.pauses.enabled
    if header and isinstance(header.get("pause_defaults"), dict):
        value = header["pause_defaults"].get("enabled")
        if isinstance(value, bool):
            enabled = value
    if config.ssmd.pause_defaults and "enabled" in config.ssmd.pause_defaults:
        enabled = bool(config.ssmd.pause_defaults["enabled"])
    return enabled


def _duration_origin(attrs: dict[str, Any], config: PlannerConfig, header: dict[str, Any]) -> str:
    if attrs.get("time") is not None:
        return "explicit"
    strength = str(attrs.get("strength", "")).lower()
    key = {
        "x-weak": "weak",
        "weak": "weak",
        "medium": "clause",
        "strong": "sentence",
        "x-strong": "paragraph",
    }.get(strength)
    if config.ssmd.pause_defaults and key in config.ssmd.pause_defaults:
        return "config_default"
    header_defaults = header.get("pause_defaults")
    if isinstance(header_defaults, dict) and header_defaults.get(key) is not None:
        try:
            parse_duration(header_defaults[key], field_name=f"pause_defaults.{key}")
        except ConfigurationError:
            return "planner_default"
        return "header_default"
    return "planner_default" if key else "none"
