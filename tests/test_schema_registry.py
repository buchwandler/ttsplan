from __future__ import annotations

import json
from pathlib import Path

from utterplan.format import schema
from utterplan.schema_registry import has_schema, schema_versions
from utterplan.versioning import (
    CURRENT_SCHEMA_VERSION,
    FORMAT,
    OLDEST_SUPPORTED_SCHEMA_VERSION,
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
)


def test_schema_registry_lists_frozen_v1() -> None:
    assert FORMAT == "utterplan"
    assert CURRENT_SCHEMA_VERSION == 1
    assert SCHEMA_VERSION == CURRENT_SCHEMA_VERSION
    assert OLDEST_SUPPORTED_SCHEMA_VERSION == 1
    assert SUPPORTED_SCHEMA_VERSIONS == (1,)
    assert schema_versions() == (1,)
    assert has_schema(1)
    assert schema(1)["properties"]["schema_version"]["const"] == 1


def test_current_schema_alias_matches_current_version() -> None:
    assert schema() == schema(CURRENT_SCHEMA_VERSION)


def test_source_and_packaged_frozen_schemas_are_identical() -> None:
    root = Path(__file__).resolve().parent.parent
    source = json.loads((root / "spec" / "schemas" / "v1.schema.json").read_text())
    packaged = json.loads((root / "utterplan" / "schemas" / "v1.schema.json").read_text())
    current_source = json.loads((root / "spec" / "utterplan.schema.json").read_text())
    current_packaged = json.loads((root / "utterplan" / "utterplan.schema.json").read_text())
    assert source == packaged == current_source == current_packaged
