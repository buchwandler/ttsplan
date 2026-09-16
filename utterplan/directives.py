from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .model import (
    AnnotationSpan,
    AudioDirective,
    EmphasisDirective,
    PlanSegment,
    PronunciationDirective,
    ProsodyDirective,
    SegmentDirectives,
    VoiceDirective,
)


def resolve_directives(
    segment: PlanSegment, annotations: tuple[AnnotationSpan, ...]
) -> PlanSegment:
    selected = sorted(
        (
            annotation
            for annotation in annotations
            if annotation.spoken_start is not None
            and annotation.spoken_end is not None
            and annotation.spoken_start <= segment.spoken_start
            and segment.spoken_end <= annotation.spoken_end
        ),
        key=lambda annotation: (
            (annotation.spoken_end or 0) - (annotation.spoken_start or 0),
            annotation.spoken_start or 0,
            annotation.id,
        ),
    )
    voice = pronunciation = prosody = emphasis = audio = None
    for annotation in selected:
        attrs = annotation.attrs
        if attrs.get("voice") or attrs.get("voice_name"):
            voice = VoiceDirective(str(attrs.get("voice") or attrs.get("voice_name")))
        phonemes = attrs.get("phonemes") or attrs.get("ph")
        if phonemes:
            pronunciation = PronunciationDirective(str(phonemes), str(attrs.get("alphabet", "ipa")))
        if any(key in attrs for key in ("rate", "pitch", "volume", "speed")):
            prosody = ProsodyDirective(
                _first(attrs, "rate", "speed"),
                _first(attrs, "pitch"),
                _first(attrs, "volume", "loudness"),
            )
        if attrs.get("emphasis") or attrs.get("level"):
            emphasis = EmphasisDirective(str(attrs.get("emphasis") or attrs.get("level")))
        src = attrs.get("audio_src") or attrs.get("src")
        if src:
            audio = AudioDirective(
                str(src),
                _first(attrs, "alt_text", "audio_alt_text"),
                _first(attrs, "clip_begin"),
                _first(attrs, "clip_end"),
                _first(attrs, "speed"),
                _first(attrs, "repeat_duration"),
                _int(attrs, "repeat_count"),
                _first(attrs, "sound_level"),
            )
    return PlanSegment(
        **{
            **{name: getattr(segment, name) for name in segment.__dataclass_fields__},
            "directives": SegmentDirectives(voice, pronunciation, prosody, emphasis, audio),
        }
    )


def _first(attrs: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = attrs.get(name)
        if value is not None:
            return str(value)
    return None


def _int(attrs: Mapping[str, Any], name: str) -> int | None:
    value = attrs.get(name)
    return int(value) if value is not None else None
