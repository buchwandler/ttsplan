---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0001
release_version: 0.1.3
kind: added
summary:
  Added explain CLI command that renders compiled plans as human-readable speech
  narratives
status: accepted
audience: null
scopes: []
source_refs:
  - git:402275374979b9372c1491072c4e29b642da523f
paths:
  - utterplan/explain.py
  - utterplan/cli.py
  - docs/cli.md
  - docs/debugging.md
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 1
---

The explain command presents prepared wording, render units, languages, resolved pauses, directives, markers, and warnings. The --details flag adds IDs, offsets, provenance, hashes, and plan identity information.
