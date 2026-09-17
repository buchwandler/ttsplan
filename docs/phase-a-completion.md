# Phase A completion and release evidence

## Scope

UtterPlan is a standalone, engine-independent planning compiler ending before
G2P and synthesis. `../pykokoro` is a read-only parity reference. This
repository does not modify PyKokoro and does not add renderer, G2P, ONNX, or
audio dependencies.

## Current release contract

- Target package release: `0.1.0`
- UtterPlan schema version: `1`
- PyKokoro parity target: the supplied sibling checkout at `../pykokoro`
- Tested migration floors: `phrasplit>=0.3.9,<0.4` and
  `spokenform>=0.4.3,<0.5`

Package and schema versions are independent. Test totals and parity corpus
sizes are intentionally not recorded as fixed status claims because they
change with the source tree. Use the release commands below for current
results.

## Verification commands

```bash
python -m pytest -q -m 'not reference'
pytest -q -m reference
ruff check .
mypy utterplan
python -m build
sphinx-build -W --keep-going -b html docs docs/_build/html
```

The reference test is optional and runs PyKokoro in a subprocess. It reports
its tested version, commit, and dependency versions. Native UtterPlan tests must
pass without the sibling checkout.

## Architectural evidence

The native suite covers parsing, language planning, preparation, spoken and
structural coordinates, boundaries, pauses, directives, markers, units, schema
validation, deterministic identity, package metadata, import boundaries, and
the public renderer-consumer contract. Plans retain only JSON-compatible
semantic state. Provider documents and runtime sessions are released before a
completed plan is returned.
