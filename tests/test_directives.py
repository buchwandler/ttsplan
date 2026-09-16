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
