# PyKokoro reference evidence

The sibling `../pykokoro` checkout is a read-only migration oracle. The normal
UtterPlan package never imports it. The optional reference test invokes the
frontend helper in a subprocess and records the PyKokoro version, Git revision,
and dependency versions on every run.

## Tested snapshot

The tested snapshot is discovered dynamically. No PyKokoro version, commit, or
fixture count is a hard-coded parity requirement. The helper reports the actual
values in its JSON output so a refreshed sibling checkout produces auditable
evidence.

The corpus includes plain text, spokenform preparation, multilingual spans,
parentheticals, paragraphs, explicit breaks, markers, pronunciation, prosody,
audio metadata, logical voices, quoted sentence boundaries, punctuation,
Unicode, empty input, and language detection metadata.

## Strict comparison policy

The migration parity test compares the renderer-facing semantic contract:

- exact spoken text;
- ordered segment text, spoken offsets, language, paragraph, sentence, and
  clause ownership;
- language runs;
- annotation spoken ranges and portable attributes;
- explicit and derived boundary positions, provenance, and resolved duration;
- marker position and ownership;
- unit ranges and segment composition.

Only documented normalizations are applied. Provider-specific annotation kind
names, concrete voice resolution metadata, whitespace-only segment records, and
language spelling variants such as `fr` and `fr-fr` are normalized. UtterPlan
remains the authority for typed directives, final pause ownership, and immutable
unit records.

| Behavior                      | PyKokoro representation             | UtterPlan representation                    |
| ----------------------------- | ----------------------------------- | ------------------------------------------- |
| Written-to-spoken preparation | Provider preparation object         | `TextPreparationInfo` and `texts.spoken`    |
| Segment content               | Frontend segments                   | `PlanSegment.text` and spoken offsets       |
| Language                      | Prepared language runs              | `plan.languages` and `PlanSegment.language` |
| Directives                    | Portable SSMD annotation attributes | Typed `SegmentDirectives`                   |
| Pauses                        | Boundary events                     | `BoundaryEvent` and resolved segment pauses |
| Markers and units             | Frontend boundary and unit grouping | `Marker` and `PlanUnit`                     |
| Provider documents            | Request-local objects               | Released before plan construction           |
| Phonemes and audio            | Renderer-specific                   | Out of scope for UtterPlan                  |

Run the optional suite with:

```bash
python -m pytest -q -m reference
```

A missing sibling checkout skips the reference test. Native tests remain usable
without PyKokoro.
