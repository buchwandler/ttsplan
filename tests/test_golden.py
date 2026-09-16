from pathlib import Path

import jsonschema

from utterplan import UtterancePlan
from utterplan.format import schema

GOLDEN = sorted(Path("tests/golden").glob("*.utterplan.json"))


def test_golden_plans_roundtrip_and_validate():
    assert GOLDEN
    for path in GOLDEN:
        plan = UtterancePlan.load(path)
        jsonschema.validate(plan.to_dict(), schema())
        assert UtterancePlan.from_json(plan.to_json()) == plan
