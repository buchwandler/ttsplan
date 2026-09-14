from ttsplan import PlannerConfig, TTSPlanner


def test_multilingual_preparation_composes_run_offsets():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan('Hello [Bonjour]{lang="fr"}.')
    assert plan.texts.spoken == "Hello Bonjour."
    assert [(run.language, run.spoken_start, run.spoken_end) for run in plan.languages] == [
        ("en-us", 0, 6),
        ("fr", 6, 13),
        ("en-us", 13, 14),
    ]
    assert plan.preparation.languages == ("en-us", "fr", "en-us")
    assert plan.preparation.offset_map["source_length"] == len(plan.texts.structural)


def test_pronunciation_annotation_is_protected_and_resolved():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan('[tomato]{ph="təˈmeɪtoʊ"}')
    assert plan.texts.spoken == "tomato"
    assert plan.segments[0].directives.pronunciation.phonemes == "təˈmeɪtoʊ"


def test_header_pause_default_and_event_anchor_are_preserved():
    text = "---\npause_defaults:\n  sentence: 0.45\n---\nHello ...s world"
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan(text)
    event = next(event for event in plan.boundaries if event.kind == "explicit")
    assert event.seconds == 0.45
    assert event.attrs["anchor"] == "after"
    assert event.attrs["pause_origin"] == "header_default"


def test_zero_break_is_not_a_paragraph_event():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello ...0ms world")
    assert any(event.kind == "explicit" and event.seconds == 0.0 for event in plan.boundaries)
    assert not any(event.kind == "paragraph" for event in plan.boundaries)
