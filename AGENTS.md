# UtterPlan development rules

1. UtterPlan is engine-independent.
2. `.utterplan.json` schema v1 is the canonical inter-package contract.
3. Python objects may not contain semantic state that cannot survive file roundtrip.
4. UtterPlan ends before G2P.
5. Core code must not import PyKokoro, PiperSynth, kokorog2p, piperg2p, ONNX Runtime, or audio packages.
6. Public UtterancePlan objects contain no phonemes, model token IDs, models, sessions, or audio.
7. Completed plans must not retain spaCy or provider documents.
8. Every offset has a documented coordinate space.
9. Default planning is deterministic.
10. Schema changes require explicit compatibility review.
11. PyKokoro tests are migration tests, not runtime dependencies.
12. Do not modify `../pykokoro` during Phase A.
