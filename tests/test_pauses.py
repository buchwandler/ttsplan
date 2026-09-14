from ttsplan import PauseConfig, PlannerConfig, TTSPlanner


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
