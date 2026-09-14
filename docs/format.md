# TTSPlan format v1

A plan is UTF-8 JSON with `format: "ttsplan"` and `schema_version: 1`. Package version and schema version are independent. The exact caller input is retained in `source`; `texts.structural` is parsed structure and `texts.spoken` is the prepared text sent toward G2P.

The top-level semantic categories are source, config, texts, preparation, languages, annotations, boundaries, tokens, segments, units, markers, warnings, diagnostics, and `plan_id`. Segments are the atomic engine-facing records. Their ranges are half-open offsets into `texts.spoken`. Units group segments by paragraph or sentence.

`plan_id` is `sha256:` followed by the SHA-256 digest of canonical semantic JSON. Canonical JSON uses UTF-8, sorted keys, compact separators, no ASCII escaping, and excludes producer, warnings, diagnostics, and identity itself. Unit hashes use the explicit `ttsplan-unit-v1` schema and contain no phonemes, models, embeddings, or audio.

Pauses contain both resolved seconds and contributing boundary IDs. Boundary records preserve kind, origin, strength, and position so a plan can answer why a renderer should pause. Directives are typed semantic requests for voice, pronunciation, prosody, emphasis, and external audio metadata.

Readers reject unsupported schema versions rather than guessing. Unknown top-level semantic fields are not accepted by the v1 schema. Extensions belong in documented metadata dictionaries.

## Coordinate and provenance rules

Annotations retain `structural_start` and `structural_end` in `texts.structural` plus nullable `spoken_start` and `spoken_end` in `texts.spoken`. Preparation stores the dependency offset map and replacements. Boundary and marker positions are always spoken coordinates; segment ranges and renderer-facing annotation applicability are also spoken coordinates.

The planner validates nested JSON shapes before constructing objects. It rejects malformed field types instead of coercing values, and validates range, ordering, reference, unit membership, hash, and plan identity invariants.
