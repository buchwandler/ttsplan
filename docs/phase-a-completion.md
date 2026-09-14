# Phase A completion report

## Scope

TTSPlan is a standalone, engine-independent planning compiler ending before G2P and synthesis. `../pykokoro` was used only as a read-only reference checkout. PyKokoro integration and Phase B remain out of scope.

## Recorded result

- TTSPlan version: `0.1.0`
- Schema version: `1`
- PyKokoro reference version: `0.9.6.dev1+g21bcf5590`
- PyKokoro reference commit: `50802ee9a70cd3eea7f2609858255dd39d3adf92`
- Native test cases: `34` passed with `pytest -m "not reference"`
- Reference test cases: `1` passed with `pytest -m reference`
- Representative golden plans: `7` plus the existing baseline
- Intentional differences: whitespace-only reference split records are normalized away; typed TTSPlan directives and resolved pause records replace provider-specific runtime objects; provider documents are released before plan construction.
- Schema changes: annotation records now require dual structural/spoken coordinates; source and packaged schemas are synchronized.
- PyKokoro modification: none. `git -C ../pykokoro status --short` was clean during completion.

## Release gate evidence

Native behavior is covered by coordinate, preparation, linguistic, boundary, pause, directive, marker, unit, schema, identity, and golden-plan tests. The reference helper runs PyKokoro in a subprocess and records its revision. Normal TTSPlan imports remain independent of PyKokoro, G2P, ONNX Runtime, and audio packages.

Before release, run:

```bash
pytest -m "not reference"
pytest -m reference
ruff check .
mypy ttsplan
python -m build
```
