# Schema history fixtures

Files under `tests/schema_history/<version>/` are immutable historical UtterPlan
fixtures. They represent released serialized plans and must not be regenerated
from the current planner.

Schema v1 remains the current schema. When a real future schema is released,
add a new version directory and keep `v1/` unchanged. Every supported historical
fixture must continue to validate against its frozen schema and load through the
public migration-aware API.
