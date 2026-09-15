# Coordinate spaces

TTSPlan uses explicit coordinate names. `spoken_start`, `spoken_end`, and `spoken_position` refer to half-open offsets into `texts.spoken`. Token, annotation-spoken, language-run, marker, unit, and segment ranges consumed by a renderer use this prepared/synthesis-space coordinate system.

`structural_start` and `structural_end` refer to half-open offsets into `texts.structural`. The source field contains exact caller input, which may include SSMD headers and markup; source offsets are not fabricated for renderer slicing.

When written-to-spoken preparation changes text, the plan stores preparation provenance and an offset map where the dependency provides one. The same composed map is used for annotations, language spans, boundaries, and markers. Renderers must use `AnnotationSpan.spoken_start` and `spoken_end` when mapping annotations into `PlanSegment.text`; structural offsets must not be used to slice prepared text.

Linguistic token fields (`spoken_start`, `spoken_end`, `text`, `pos`, `tag`, `lemma`, and `language`) are self-contained and refer to prepared text. Provider documents are not part of the public plan.
