import json
from pathlib import Path

import pytest

from ttsplan import PlanFormatError, PlannerConfig, TTSPlan, TTSPlanner
from ttsplan.format import schema


def test_source_and_packaged_schema_are_identical():
    source = json.loads(Path("spec/ttsplan.schema.json").read_text())
    packaged = json.loads(Path("ttsplan/ttsplan.schema.json").read_text())
    assert packaged == source
    assert schema() == source


def test_nested_text_types_are_not_coerced():
    value = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello.").to_dict()
    value["texts"]["spoken"] = 123
    with pytest.raises(PlanFormatError, match="field.type"):
        TTSPlan.from_dict(value)


def test_unknown_preparation_key_is_rejected():
    value = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello.").to_dict()
    value["preparation"]["unexpected"] = True
    with pytest.raises(PlanFormatError, match="preparation"):
        TTSPlan.from_dict(value)
