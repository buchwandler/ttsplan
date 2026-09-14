from ttsplan import PlannerConfig, TTSPlanner


def test_spokenform_mapping_keeps_structural_and_spoken_ranges_distinct():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan(
        "Dr. Smith bought 5 kg on Jan. 4."
    )
    assert plan.texts.structural != plan.texts.spoken
    annotation = plan.annotations[0]
    assert (annotation.structural_start, annotation.structural_end) == (0, 32)
    assert (annotation.spoken_start, annotation.spoken_end) == (0, len(plan.texts.spoken))
    mapping = plan.preparation.offset_map
    assert mapping["source_length"] == len(plan.texts.structural)
    assert mapping["output_length"] == len(plan.texts.spoken)
    assert mapping["source_left"][17] != round(17 * len(plan.texts.spoken) / len(plan.texts.structural))


def test_identity_mapping_is_exact():
    text = "One. Two."
    plan = TTSPlanner(
        PlannerConfig(language="en-us", document_format="plain", text_preparation="identity")
    ).plan(text)
    assert plan.texts.structural == plan.texts.spoken == text
    mapping = plan.preparation.offset_map
    assert mapping["source_left"] == list(range(len(text) + 1))
    assert mapping["output_right"] == list(range(len(text) + 1))
    for annotation in plan.annotations:
        assert annotation.spoken_start == annotation.structural_start
        assert annotation.spoken_end == annotation.structural_end


def test_segment_membership_uses_spoken_ranges():
    plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Doctor bought 5 kg.")
    assert plan.tokens
    assert all(index < len(plan.tokens) for segment in plan.segments for index in segment.token_indices)
