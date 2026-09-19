---
schema_version: 2
object_type: release_entry
versioning:
  schema_version: 1
  revision: 2
entry_id: entry-0002
release_version: 0.1.3
kind: changed
summary:
  Improved consumer contract with stable renderer input view and directive
  handling
status: accepted
audience: null
scopes: []
source_refs:
  - git:2c64e291f0e568310afb7ca5e770ef2b691d9452
paths:
  - utterplan/directives.py
  - utterplan/model.py
  - utterplan/parsers.py
  - utterplan/planner.py
  - docs/consumer-guide.md
issues: []
prs: []
sources: []
contributors: []
breaking: false
internal: false
order: 2
---

Consumers may now rely on documented plan-level fields for renderer input. Directive handling was improved with better pause policy and PyKokoro migration parity. The consumer guide documents the immutability contract for completed plans.
