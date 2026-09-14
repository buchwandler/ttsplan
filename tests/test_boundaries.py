from ttsplan import PlannerConfig, TTSPlanner


def test_parenthetical_boundary_keeps_phrasplit_origin():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan(
        "They changed out their clothes (stained with blood)."
    )
    events = [event for event in plan.boundaries if event.kind == "parenthetical"]
    assert events
    assert all(event.origin == "phrasplit" for event in events)
    assert all(0 <= event.position <= len(plan.texts.spoken) for event in events)


def test_language_cut_does_not_invent_clausal_comma():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan('Hello [Bonjour]{lang="fr"}.')
    assert not any(event.kind == "clausal_comma" for event in plan.boundaries)


def test_explicit_ssmd_boundary_keeps_ssmd_origin():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello ...c world")
    event = next(event for event in plan.boundaries if event.kind == "explicit")
    assert event.origin == "ssmd"
    assert event.attrs["anchor"] == "after"
