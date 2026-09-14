# ttsplan

TTSPlan is an engine-independent TTS planning compiler and interchange format. It converts text and speech markup into deterministic, human-readable synthesis plans containing spoken text, language runs, segments, pauses, directives, markers, and render units. TTSPlan performs no phonemization or audio synthesis.

```bash
ttsplan compile chapter.ssmd --language en-us -o chapter.ttsplan.json
ttsplan inspect chapter.ttsplan.json
ttsplan validate chapter.ttsplan.json
```

```python
from ttsplan import PlannerConfig, TTSPlanner, TTSPlan

planner = TTSPlanner(PlannerConfig(language="en-us"))
plan = planner.plan("Doctor Smith bought 5 kg of apples.")
plan.save("example.ttsplan.json")
assert TTSPlan.load("example.ttsplan.json") == plan
```

The `.ttsplan.json` file is the primary boundary between planning and rendering. It contains no phonemes, model tokens, model sessions, audio, or renderer configuration. PyKokoro is only an optional read-only parity reference during development.


Phase A includes an optional subprocess parity suite against the recorded PyKokoro revision. The normal package remains independent and imports no renderer, G2P, ONNX, or audio packages.
See [docs/format.md](docs/format.md), [docs/architecture.md](docs/architecture.md), and [docs/debugging.md](docs/debugging.md).
