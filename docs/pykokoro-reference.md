# PyKokoro reference

The sibling `../pykokoro` checkout is a read-only migration oracle. Phase A production code never imports it. Reference tests, when enabled, run the sibling in a subprocess and compare normalized engine-neutral semantics only.

Repository: `../pykokoro`
Reference version: `0.9.6.dev1+g21bcf5590`
Reference commit: `50802ee9a70cd3eea7f2609858255dd39d3adf92`

## Comparison policy

The subprocess helper `tests/reference/dump_pykokoro_frontend.py` runs `prepare_frontend()` with spaCy disabled and emits normalized structural text, spoken text, preparation replacements and warnings, annotations, boundaries, and segments. TTSPlan compares spoken text and non-whitespace segment content exactly. PyKokoro whitespace-only split records are omitted from the normalized comparison.

| Behavior | PyKokoro representation | TTSPlan representation | Equivalent? | Reason | Regression test |
| --- | --- | --- | --- | --- | --- |
| Offset mapping | Provider `OffsetMap` | Serialized structural-to-spoken map with dual annotation coordinates | Yes | Same source and output ranges are compared | `tests/test_coordinates.py` |
| Pause resolution | Runtime boundary handling | Typed `ResolvedPause` with contributing event IDs | Yes | Renderer-neutral duration is retained earlier | `tests/test_pauses.py` |
| Voice binding | Provider voice name may be resolved later | Logical voice reference plus document bindings | Yes | Provider voice resolution is out of scope | `tests/test_planner.py` |
| Provider documents | Request-local spaCy documents | Released before plan construction | Yes | Public plan remains JSON-compatible | `tests/test_linguistics.py` |
| Whitespace-only segments | Split records can contain whitespace | Empty/whitespace records are omitted | Yes | No synthesized speech content is lost | `tests/reference/test_pykokoro_parity.py` |

Phonemes, model token IDs, audio, ONNX runtime, embeddings, timestamps, and acoustic short-sentence handling are intentionally outside frontend parity.
