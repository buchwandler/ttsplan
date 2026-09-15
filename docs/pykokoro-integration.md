# PyKokoro integration boundary

TTSPlan is an independent planning compiler. PyKokoro is an optional consumer
and parity oracle, not a runtime dependency of this package.

The intended migration keeps the existing PyKokoro user API unchanged:

```text
KokoroPipeline.run(text)
    -> map PipelineConfig and GenerationConfig to PlannerConfig
    -> TTSPlanner.plan(text)
    -> adapt public PlanSegment records to PyKokoro's G2P input
    -> PyKokoro G2P
    -> phoneme processing
    -> model inference
    -> audio
```

PyKokoro owns model selection, voice assets, G2P, model tokens, ONNX sessions,
acoustic behavior, audio, and any compatibility behavior specific to its
renderer. TTSPlan owns deterministic document parsing, language planning,
written-to-spoken preparation, segmentation, semantic directives, boundaries,
pauses, markers, and render units.

## Thin adapter inputs

A future adapter can use only public TTSPlan fields:

- `plan.texts.spoken`;
- `plan.languages`;
- `plan.tokens` and `plan.annotations`;
- `plan.boundaries`;
- `plan.segments` and `plan.units`;
- `plan.markers`;
- `plan.document_metadata`;
- resolved segment pauses and typed directives.

It should pass `PlanSegment.text` and `PlanSegment.language` to the next
frontend stage. No JSON serialization is required for in-process use.

## Pause behavior

TTSPlan resolves deterministic base semantic pauses. PyKokoro may apply
renderer or acoustic variance after consuming the plan when legacy behavior
requires it. Such variance must remain outside semantic plan identity and must
not be added to TTSPlan merely to mirror renderer settings.

## Reference parity

The optional reference suite runs PyKokoro in a subprocess and compares
normalized engine-neutral semantics. It does not compare phonemes, model token
IDs, sessions, audio, or model-derived timings. The pinned version, revision,
and dependency versions used for a parity run belong in the reference evidence
page, not in TTSPlan runtime metadata.
