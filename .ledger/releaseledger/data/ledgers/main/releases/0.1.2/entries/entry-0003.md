---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 1
entry_id: entry-0003
release_version: 0.1.2
kind: added
summary: Added schema versioning with frozen v1 schema and migration framework
status: accepted
audience: null
scopes: []
source_refs:
  - git:66a88b6a7fbe4cf9e0247cfd81675050f5934fea
paths:
  - utterplan/migration.py
  - utterplan/schema_registry.py
  - utterplan/schemas/v1.schema.json
  - tests/schema_history/v1/basic.json
  - tests/schema_history/v1/directives.json
  - tests/schema_history/v1/markers.json
  - tests/schema_history/v1/multilingual.json
  - tests/schema_history/v1/parenthetical.json
  - tests/schema_history/v1/spokenform_offsets.json
  - tests/schema_history/v1/ssmd_breaks.json
  - tests/test_migration_framework.py
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 3
---

Schema v1 is frozen and packaged under a versioned schema-history path. UtterPlan can inspect and migrate supported historical plan JSON before constructing the current UtterancePlan. Migration is representation conversion, not replanning. The migrate command supports --check and refuses output overwrite unless --force is supplied.
