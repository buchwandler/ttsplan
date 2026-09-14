from __future__ import annotations

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
    selected = [
        a
        for a in annotations
        if a.structural_start <= segment.spoken_start and segment.spoken_end <= a.structural_end
    ]
    voice = pronunciation = prosody = emphasis = audio = None
    for annotation in selected:
        attrs = annotation.attrs
        if attrs.get("voice") or attrs.get("voice_name"):
            voice = VoiceDirective(str(attrs.get("voice") or attrs.get("voice_name")))
        if attrs.get("phonemes") or attrs.get("ph"):
            pronunciation = PronunciationDirective(
                str(attrs.get("phonemes") or attrs.get("ph")), str(attrs.get("alphabet", "ipa"))
            )
        if any(key in attrs for key in ("rate", "pitch", "volume")):
            prosody = ProsodyDirective(attrs.get("rate"), attrs.get("pitch"), attrs.get("volume"))
        if attrs.get("emphasis") or attrs.get("level"):
            emphasis = EmphasisDirective(str(attrs.get("emphasis") or attrs.get("level")))
        if attrs.get("audio_src") or attrs.get("src"):
            audio = AudioDirective(
                str(attrs.get("audio_src") or attrs.get("src")),
                attrs.get("alt_text") or attrs.get("audio_alt_text"),
                attrs.get("clip_begin"),
                attrs.get("clip_end"),
            )
    return PlanSegment(
        **{
            **{name: getattr(segment, name) for name in segment.__dataclass_fields__},
            "directives": SegmentDirectives(voice, pronunciation, prosody, emphasis, audio),
        }
    )
