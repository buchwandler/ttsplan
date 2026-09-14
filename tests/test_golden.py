from pathlib import Path

import jsonschema

from ttsplan import TTSPlan
from ttsplan.format import schema

GOLDEN = sorted(Path("tests/golden").glob("*.ttsplan.json"))


def test_golden_plans_roundtrip_and_validate():
    assert GOLDEN
    for path in GOLDEN:
        plan = TTSPlan.load(path)
        jsonschema.validate(plan.to_dict(), schema())
        assert TTSPlan.from_json(plan.to_json()) == plan
