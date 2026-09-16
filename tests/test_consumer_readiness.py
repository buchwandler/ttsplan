from __future__ import annotations

import pytest

from ttsplan import PauseConfig, PlanFormatError, PlannerConfig, SSMDConfig, TTSPlanner


def test_reusable_planner_isolates_request_configuration() -> None:
    base = PlannerConfig(
        language="en-us", document_format="plain", text_preparation="identity", unit="sentence"
    )
    alternate = PlannerConfig(
        language="de-de",
        document_format="plain",
        text_preparation="identity",
        unit="paragraph",
        pauses=PauseConfig(sentence="180ms"),
    )
    planner = TTSPlanner(base)
    first = planner.plan("One. Two.", unit="sentence")
    second = planner.plan("Eins. Zwei.", config=alternate)
    third = planner.plan("One. Two.", unit="sentence")
    fresh = TTSPlanner(base).plan("One. Two.", unit="sentence")
    assert first == fresh == third
    assert second.config["language"] == "de-de"
    assert second.config["pauses"]["sentence"] == 0.18
    assert planner.config == base
    planner.close()


def test_duration_spellings_have_equal_plan_identity() -> None:
    left = PlannerConfig(
        language="en-us",
        document_format="plain",
        text_preparation="identity",
        pauses=PauseConfig(sentence="500ms"),
    )
    right = PlannerConfig(
        language="en-us",
        document_format="plain",
        text_preparation="identity",
        pauses=PauseConfig(sentence=0.5),
    )
    assert TTSPlanner(left).plan("One. Two.").plan_id == TTSPlanner(right).plan("One. Two.").plan_id


def _ssmd_plan(text: str, **kwargs: object):
    config = PlannerConfig(language="en-us", text_preparation="identity", ssmd=SSMDConfig(**kwargs))
    return TTSPlanner(config).plan(text)


def test_ssmd_header_unknown_key_policies() -> None:
    text = "---\nunknown: true\n---\nHello."
    warned = _ssmd_plan(text, unknown_header="warn")
    assert any("unknown SSMD header" in warning for warning in warned.warnings)
    ignored = _ssmd_plan(text, unknown_header="ignore")
    assert not ignored.warnings
    with pytest.raises(PlanFormatError, match="header.unknown"):
        _ssmd_plan(text, unknown_header="error")


def test_ssmd_header_malformed_yaml_is_public_error() -> None:
    with pytest.raises(PlanFormatError, match="header.yaml_invalid"):
        _ssmd_plan("---\npause_defaults: [\n---\nHello.")


def test_ssmd_header_invalid_pause_values_follow_strict_policy() -> None:
    text = "---\npause_defaults:\n  sentence: fast\n---\nHello ...s world"
    with pytest.raises(PlanFormatError, match="header.invalid"):
        _ssmd_plan(text)
    relaxed = _ssmd_plan(text, strict_header=False)
    assert any("pause_defaults.sentence" in warning for warning in relaxed.warnings)


def test_ssmd_parse_header_false_does_not_consume_front_matter() -> None:
    plan = _ssmd_plan("---\nunknown: [\n---\nHello.", parse_header=False)
    assert plan.texts.structural.startswith("---")


def test_pause_defaults_enabled_disables_automatic_document_pauses() -> None:
    plan = _ssmd_plan("---\npause_defaults:\n  enabled: false\n---\nOne. Two.")
    assert all(
        segment.pause_before.seconds == 0 and segment.pause_after.seconds == 0
        for segment in plan.segments
    )


def test_voice_change_pause_uses_logical_voice_in_one_language() -> None:
    config = PlannerConfig(
        language="en-us", text_preparation="identity", pauses=PauseConfig(mode="auto")
    )
    plan = TTSPlanner(config).plan('[One]{voice="a"} [Two]{voice="b"}.')
    voice_events = [event for event in plan.boundaries if event.kind == "voice_change"]
    assert voice_events
    assert any(
        event_id in plan.segments[0].pause_after.events
        for event_id in (event.id for event in voice_events)
    )


def test_prepared_contract_uses_spoken_coordinates_and_public_token_fields() -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Dr. Smith has 5 kg.")
    assert plan.texts.spoken == "Doctor Smith has five kilograms."
    assert plan.annotations[0].spoken_end == len(plan.texts.spoken)
    assert all(token.spoken_end <= len(plan.texts.spoken) for token in plan.tokens)
    assert all(
        hasattr(token, field)
        for token in plan.tokens
        for field in ("text", "pos", "tag", "lemma", "language")
    )
    assert all(
        segment.text == plan.texts.spoken[segment.spoken_start : segment.spoken_end]
        for segment in plan.segments
    )


def test_voice_bindings_and_segment_logical_voice_remain_separate() -> None:
    text = '---\nvoice_bindings:\n  narrator: voice-a\n---\n[Hello]{voice="narrator"}.'
    plan = TTSPlanner(PlannerConfig(language="en-us", text_preparation="identity")).plan(text)
    assert plan.document_metadata["voice_bindings"] == {"narrator": "voice-a"}
    assert plan.segments[0].directives.voice.reference == "narrator"
    assert plan.segments[0].directives.voice.reference != "voice-a"
    assert "offset_map" not in plan.to_dict()["preparation"]
    assert plan == type(plan).from_json(plan.to_json())
