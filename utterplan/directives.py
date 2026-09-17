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
        voice_reference = _first(attrs, "voice", "voice_name")
        if voice_reference:
            voice = VoiceDirective(voice_reference)
        phonemes = _first(attrs, "ph", "phonemes")
        if phonemes:
            pronunciation = PronunciationDirective(phonemes, _first(attrs, "alphabet") or "ipa")
        if any(
            key in attrs
            for key in (
                "rate",
                "prosody_rate",
                "pitch",
                "prosody_pitch",
                "volume",
                "prosody_volume",
                "speed",
            )
        ):
            prosody = ProsodyDirective(
                _first(attrs, "rate", "prosody_rate", "speed"),
                _first(attrs, "pitch", "prosody_pitch"),
                _first(attrs, "volume", "prosody_volume", "loudness"),
            )
        emphasis_level = _first(attrs, "emphasis", "level")
        if emphasis_level:
            emphasis = EmphasisDirective(emphasis_level)
        src = _first(attrs, "src", "audio_src")
        if src:
            audio = AudioDirective(
                src,
                _first(attrs, "alt_text", "audio_alt_text"),
                _first(attrs, "clip_begin", "audio_clip_begin"),
                _first(attrs, "clip_end", "audio_clip_end"),
                _first(attrs, "speed", "audio_speed"),
                _first(attrs, "repeat_duration", "repeat_dur", "audio_repeat_dur"),
                _int(attrs, "repeat_count", "audio_repeat_count"),
                _first(attrs, "sound_level", "audio_sound_level"),
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


def _int(attrs: Mapping[str, Any], *names: str) -> int | None:
    value = _first(attrs, *names)
    return int(value) if value is not None else None
