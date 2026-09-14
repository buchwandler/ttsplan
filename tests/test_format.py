import json

import pytest

from ttsplan import PlannerConfig, PlanValidationError, TTSPlan, TTSPlanner, UnsupportedSchemaError
from ttsplan.format import schema


def plan():
    return TTSPlanner(PlannerConfig(language="en-us")).plan("Doctor Smith bought 5 kg.")


def test_roundtrip_all_apis(tmp_path):
    original = plan()
    assert TTSPlan.from_dict(original.to_dict()) == original
    assert TTSPlan.from_json(original.to_json()) == original
    path = tmp_path / "plan.ttsplan.json"
    original.save(path)
    assert TTSPlan.load(path) == original
    assert TTSPlan.load(path).plan_id == original.plan_id


def test_schema_and_determinism():
    import jsonschema

    value = plan().to_dict()
    jsonschema.validate(value, schema())
    assert plan().to_dict() == plan().to_dict()


def test_unsupported_schema():
    value = plan().to_dict()
    value["schema_version"] = 2
    with pytest.raises(UnsupportedSchemaError):
        TTSPlan.from_dict(value)


def test_semantic_corruption_is_rejected():
    value = plan().to_dict()
    value["segments"][0]["text"] = "wrong"
    with pytest.raises(PlanValidationError):
        TTSPlan.from_dict(value)


def test_json_is_plain_data():
    value = json.loads(plan().to_json())
    assert "phonemes" not in json.dumps(value)
    assert "numpy" not in json.dumps(value)
