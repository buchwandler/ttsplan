import pytest

from utterplan import PlannerConfig, UtterancePlanner


def test_directives_use_spoken_annotation_ranges_and_membership():
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        '[fast]{rate="1.2" pitch="+2st" volume="80%" emphasis="strong"}'
    )
    segment = plan.segments[0]
    assert segment.directives.prosody.rate == "1.2"
    assert segment.directives.prosody.pitch == "+2st"
    assert segment.directives.prosody.volume == "80%"
    assert segment.directives.emphasis.level == "strong"
    assert segment.annotation_ids
    assert segment.token_indices


def test_audio_directive_preserves_supported_engine_neutral_metadata():
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        '[sound]{src="clip.wav" alt_text="sound" speed="1.2" repeat_count="2" sound_level="-3dB"}'
    )
    audio = plan.segments[0].directives.audio
    assert audio.src == "clip.wav"
    assert audio.speed == "1.2"
    assert audio.repeat_count == 2
    assert audio.sound_level == "-3dB"
    assert plan == type(plan).from_json(plan.to_json())


@pytest.mark.parametrize(
    ("attribute", "value", "field"),
    [
        ("src", "clip.wav", "src"),
        ("audio_src", "clip.wav", "src"),
        ("alt_text", "alt", "alt_text"),
        ("audio_alt_text", "alt", "alt_text"),
        ("clip_begin", "1s", "clip_begin"),
        ("audio_clip_begin", "1s", "clip_begin"),
        ("clip_end", "2s", "clip_end"),
        ("audio_clip_end", "2s", "clip_end"),
        ("speed", "1.2", "speed"),
        ("audio_speed", "1.2", "speed"),
        ("repeat_duration", "3s", "repeat_duration"),
        ("repeat_dur", "3s", "repeat_duration"),
        ("audio_repeat_dur", "3s", "repeat_duration"),
        ("repeat_count", "2", "repeat_count"),
        ("audio_repeat_count", "2", "repeat_count"),
        ("sound_level", "-3dB", "sound_level"),
        ("audio_sound_level", "-3dB", "sound_level"),
    ],
)
def test_audio_directive_aliases(attribute: str, value: str, field: str) -> None:
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        f'[sound]{{src="clip.wav" {attribute}="{value}"}}'
    )
    audio = plan.segments[0].directives.audio
    assert audio is not None
    assert getattr(audio, field) == (int(value) if field == "repeat_count" else value)


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [("rate", "1.2"), ("prosody_rate", "1.2")],
)
def test_prosody_rate_aliases(attribute: str, expected: str) -> None:
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        f'[fast]{{{attribute}="{expected}"}}'
    )
    assert plan.segments[0].directives.prosody.rate == expected


@pytest.mark.parametrize(
    ("attribute", "field", "value"),
    [
        ("pitch", "pitch", "+2st"),
        ("prosody_pitch", "pitch", "+2st"),
        ("volume", "volume", "80%"),
        ("prosody_volume", "volume", "80%"),
    ],
)
def test_prosody_aliases(attribute: str, field: str, value: str) -> None:
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        f'[fast]{{{attribute}="{value}"}}'
    )
    assert getattr(plan.segments[0].directives.prosody, field) == value


@pytest.mark.parametrize("attribute", ["ph", "phonemes"])
def test_pronunciation_aliases(attribute: str) -> None:
    plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(
        f'[word]{{{attribute}="dʒɪf" alphabet="ipa"}}'
    )
    pronunciation = plan.segments[0].directives.pronunciation
    assert pronunciation is not None
    assert pronunciation.phonemes == "dʒɪf"
    assert pronunciation.alphabet == "ipa"
