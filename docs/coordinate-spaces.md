# Coordinate spaces

TTSPlan uses explicit coordinate names. `spoken_start`, `spoken_end`, and `spoken_position` refer to half-open offsets into `texts.spoken`. Token and segment ranges use the same synthesis-space coordinates. Structural annotation ranges refer to `texts.structural` unless a field says otherwise.

The source field contains exact caller input, which can include SSMD headers and markup. TTSPlan does not fabricate offsets into source markup. When preparation changes text, it stores preparation provenance and an offset map where the dependency provides one. A renderer should use spoken ranges for synthesis.

An identity preparation has an exact one-to-one map. Spokenform preparation uses its actual `OffsetMap`, including non-linear replacements, and the same composed map is used for annotations, language spans, boundaries, markers, and other structural events.
