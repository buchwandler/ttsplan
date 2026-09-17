from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema

from utterplan import UtterancePlan
from utterplan.format import schema

ROOT = Path(__file__).resolve().parent
FIXTURES = sorted((ROOT / "schema_history" / "v1").glob("*.json"))


def test_v1_fixtures_are_present() -> None:
    assert len(FIXTURES) >= 5


def test_v1_fixtures_validate_and_load_without_mutation() -> None:
    frozen_schema = schema(1)
    for path in FIXTURES:
        value = json.loads(path.read_text(encoding="utf-8"))
        before = copy.deepcopy(value)
        assert value["format"] == "utterplan"
        assert value["schema_version"] == 1
        jsonschema.validate(value, frozen_schema)
        plan = UtterancePlan.from_dict(value)
        assert plan.plan_id == value["plan_id"]
        assert plan.source.text == value["source"]["text"]
        assert plan.texts.spoken == value["texts"]["spoken"]
        assert value == before


def test_every_supported_schema_has_a_registry_entry() -> None:
    from utterplan.schema_registry import has_schema
    from utterplan.versioning import SUPPORTED_SCHEMA_VERSIONS

    assert all(has_schema(version) for version in SUPPORTED_SCHEMA_VERSIONS)
