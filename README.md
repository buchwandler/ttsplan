# ttsplan

TTSPlan is an engine-independent TTS planning compiler and interchange format. It converts text and speech markup into deterministic, human-readable semantic speech plans containing prepared spoken text, language runs, segments, pauses, directives, markers, and render units. TTSPlan performs no phonemization, model adaptation, inference, or audio synthesis.

```bash
ttsplan compile chapter.ssmd --language en-us -o chapter.ttsplan.json
ttsplan inspect chapter.ttsplan.json
ttsplan validate chapter.ttsplan.json
```

```python
from ttsplan import PlannerConfig, TTSPlan, TTSPlanner

planner = TTSPlanner(PlannerConfig(language="en-us"))
plan = planner.plan("Doctor Smith bought 5 kg of apples.")
plan.save("example.ttsplan.json")
assert TTSPlan.load("example.ttsplan.json") == plan
```

## Renderer-consumer boundary

The supported in-process API is `PlannerConfig`, `TTSPlanner`, and `TTSPlan`. A renderer may consume the immutable `TTSPlan` Python object directly; JSON is the portable persistence and semantic interchange form, not a required in-process round trip. The serialized schema defines the semantic interchange contract and the Python model is its supported in-process representation.

TTSPlan owns the source-to-plan boundary:

```text
source text / SSMD -> prepared semantic speech plan -> external renderer
                                                 -> engine-specific G2P and speech
```

Renderers consume `PlanSegment.text`, which is prepared/spoken text, and use `spoken_start`/`spoken_end` for prepared-text coordinates. Annotation spans and linguistic tokens likewise expose spoken coordinates. `PlanSegment.pause_before` and `pause_after` are already-resolved semantic pauses; consumers must not recompute pause policy. Logical voice references and document `voice_bindings` remain engine-neutral and are never resolved to concrete engine voice IDs.

Plans contain no phonemes, model tokens, model sessions, audio, renderer configuration, or provider documents. Linguistic resources and provider objects are request-local. A planner is reusable for sequential requests; concurrent use is not promised unless the caller synchronizes access.

## Versions

The package version is dynamically derived from Git tags by setuptools-scm. A tag such as `v0.2.0` produces package version `0.2.0`; development and dirty checkouts use PEP 440 development versions. Release CI requires a matching release tag and verifies wheel, sdist, runtime, and metadata versions. The package version and TTSPlan `schema_version` are independent: releasing the package does not imply a schema change.

## Development

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
ruff check .
mypy ttsplan
python -m build
```

The `.ttsplan.json` file is the planning/rendering boundary. PyKokoro is only an optional read-only parity reference during development. The normal package remains independent and imports no renderer, G2P, ONNX, or audio packages.

See [docs/format.md](docs/format.md), [docs/architecture.md](docs/architecture.md), [docs/coordinate-spaces.md](docs/coordinate-spaces.md), and [docs/debugging.md](docs/debugging.md).
