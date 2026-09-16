import pytest

from ttsplan import PauseConfig, PlannerConfig, TTSPlanner

TEXT = "The backup battery (still warm from the morning test) sat beside the console."


def test_pause_mode_keeps_sentence_and_paragraph_policy_deterministic():
    text = "One sentence. Two sentences.\n\nSecond paragraph."
    for mode in ("tts", "manual", "auto"):
        plan = TTSPlanner(
            PlannerConfig(language="en-us", document_format="plain", pauses=PauseConfig(mode=mode))
        ).plan(text)
        assert plan.segments[0].pause_after.seconds == 0.6
        assert plan.segments[1].pause_after.seconds == 1.0


def test_automatic_parenthetical_pause_only_applies_in_auto_mode():
    text = "They changed out their clothes (stained with blood)."
    tts = TTSPlanner(PlannerConfig(language="en-us", pauses=PauseConfig(mode="tts"))).plan(text)
    auto = TTSPlanner(PlannerConfig(language="en-us", pauses=PauseConfig(mode="auto"))).plan(text)
    assert all(
        event_id not in {event.id for event in tts.boundaries if event.kind == "parenthetical"}
        for segment in tts.segments
        for event_id in segment.pause_before.events + segment.pause_after.events
    )
    assert any(
        event_id in {event.id for event in auto.boundaries if event.kind == "parenthetical"}
        for segment in auto.segments
        for event_id in segment.pause_before.events + segment.pause_after.events
    )


@pytest.mark.parametrize("mode", ["tts", "manual"])
def test_inactive_automatic_parentheticals_do_not_split_segments(mode: str):
    plan = TTSPlanner(
        PlannerConfig(
            language="en-us",
            text_preparation="identity",
            pauses=PauseConfig(mode=mode),
        )
    ).plan(TEXT)

    assert [segment.text for segment in plan.segments] == [TEXT]
    assert any(event.kind == "parenthetical" for event in plan.boundaries)
    assert all(
        not (segment.pause_before.events or segment.pause_after.events) for segment in plan.segments
    )


def test_disabled_automatic_parentheticals_do_not_split_segments():
    plan = TTSPlanner(
        PlannerConfig(
            language="en-us",
            text_preparation="identity",
            pauses=PauseConfig(mode="auto", enabled=False),
        )
    ).plan(TEXT)

    assert [segment.text for segment in plan.segments] == [TEXT]
    assert any(event.kind == "parenthetical" for event in plan.boundaries)


def test_auto_parenthetical_pauses_own_both_segment_edges():
    plan = TTSPlanner(
        PlannerConfig(
            language="en-us",
            text_preparation="identity",
            pauses=PauseConfig(mode="auto", parenthetical=0.15),
        )
    ).plan(TEXT)
    opening_event, closing_event = (
        event for event in plan.boundaries if event.kind == "parenthetical"
    )

    assert [segment.text for segment in plan.segments] == [
        "The backup battery ",
        "(still warm from the morning test)",
        " sat beside the console.",
    ]
    aside = plan.segments[1]
    resumed = plan.segments[2]
    assert aside.pause_before.seconds == pytest.approx(0.15)
    assert aside.pause_before.events == (opening_event.id,)
    assert resumed.pause_before.seconds == pytest.approx(0.15)
    assert resumed.pause_before.events == (closing_event.id,)
    assert not aside.pause_after.events
    assert not resumed.pause_after.events


def test_parenthetical_closing_pause_coexists_with_paragraph_pause():
    text = TEXT + "\n\nThe team continued the test."
    plan = TTSPlanner(
        PlannerConfig(
            language="en-us",
            text_preparation="identity",
            pauses=PauseConfig(mode="auto", parenthetical=0.15),
        )
    ).plan(text)
    resumed = next(
        segment for segment in plan.segments if segment.text == " sat beside the console."
    )

    assert resumed.pause_before.seconds == pytest.approx(0.15)
    assert resumed.pause_after.seconds == pytest.approx(1.0)


def test_explicit_ssmd_break_remains_active_when_automatic_pauses_are_disabled():
    plan = TTSPlanner(
        PlannerConfig(
            language="en-us",
            text_preparation="identity",
            pauses=PauseConfig(mode="manual", enabled=False),
        )
    ).plan("Hello ...c world")

    event = next(event for event in plan.boundaries if event.kind == "explicit")
    assert event.attrs["anchor"] == "after"
    assert any(event.id in segment.pause_after.events for segment in plan.segments)


def test_default_pause_mode_remains_tts():
    assert PauseConfig().mode == "tts"
