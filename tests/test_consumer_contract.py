from __future__ import annotations

import math

import pytest

from ttsplan import PauseConfig, PlannerConfig, TTSPlan, TTSPlanner


def assert_public_consumer_contract(plan: TTSPlan) -> None:
    segments = {segment.id: segment for segment in plan.segments}
    annotations = {annotation.id: annotation for annotation in plan.annotations}
    markers = {marker.id: marker for marker in plan.markers}
    assert len(segments) == len(plan.segments)

    for segment in plan.segments:
        assert segment.text == plan.texts.spoken[segment.spoken_start : segment.spoken_end]
        assert segment.language
        assert all(token_index < len(plan.tokens) for token_index in segment.token_indices)
        assert all(annotation_id in annotations for annotation_id in segment.annotation_ids)
        assert math.isfinite(segment.pause_before.seconds)
        assert math.isfinite(segment.pause_after.seconds)
        assert segment.pause_before.seconds >= 0
        assert segment.pause_after.seconds >= 0

    for unit in plan.units:
        assert all(segment_id in segments for segment_id in unit.segment_ids)
        assert all(marker_id in markers for marker_id in unit.marker_ids)

    restored = TTSPlan.from_json(plan.to_json())
    assert restored == plan
    assert restored.texts.spoken == plan.texts.spoken
    assert [segment.text for segment in restored.segments] == [
        segment.text for segment in plan.segments
    ]


def test_plain_spokenform_consumer_contract() -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Dr. Smith has 5 kg.")
    assert plan.texts.spoken == "Doctor Smith has five kilograms."
    assert_public_consumer_contract(plan)


def test_multilingual_ssmd_consumer_contract() -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us", text_preparation="identity")).plan(
        'Hello [Bonjour]{lang="fr"}.'
    )
    assert {run.language for run in plan.languages} == {"en-us", "fr"}
    assert_public_consumer_contract(plan)


def test_voice_directive_and_document_binding_are_public() -> None:
    text = '---\nvoice_bindings:\n  narrator: voice-a\n---\n[Hello]{voice="narrator"}.'
    plan = TTSPlanner(PlannerConfig(language="en-us", text_preparation="identity")).plan(text)
    assert plan.document_metadata["voice_bindings"] == {"narrator": "voice-a"}
    assert plan.segments[0].directives.voice.reference == "narrator"
    assert_public_consumer_contract(plan)


def test_explicit_break_is_a_public_boundary() -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us", text_preparation="identity")).plan(
        "Hello ...c world"
    )
    assert any(boundary.kind == "explicit" for boundary in plan.boundaries)
    assert_public_consumer_contract(plan)


def test_automatic_semantic_pauses_are_resolved() -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us", pauses=PauseConfig(mode="auto"))).plan(
        "They changed clothes (stained with blood)."
    )
    parenthetical_ids = {event.id for event in plan.boundaries if event.kind == "parenthetical"}
    assert parenthetical_ids
    assert any(
        parenthetical_id in segment.pause_before.events + segment.pause_after.events
        for segment in plan.segments
        for parenthetical_id in parenthetical_ids
    )
    assert_public_consumer_contract(plan)


@pytest.mark.parametrize("unit", ["paragraph", "sentence"])
def test_markers_and_unit_ownership_are_public(unit: str) -> None:
    plan = TTSPlanner(PlannerConfig(language="en-us", unit=unit, text_preparation="identity")).plan(
        "One. @mark Two."
    )
    assert plan.markers
    owned = [marker_id for item in plan.units for marker_id in item.marker_ids]
    assert owned == [plan.markers[0].id]
    assert_public_consumer_contract(plan)
