# PyKokoro reference evidence

The sibling `../pykokoro` checkout is a read-only migration oracle. The normal
UtterPlan package never imports it. The optional reference test invokes the
frontend helper in a subprocess and compares normalized, engine-neutral
semantics.

## Tested snapshot

The current parity run used:

- PyKokoro version: `0.9.8`
- PyKokoro commit: `cc4271515011cbbe8843fc3673393063044c22e9`
- `phrasplit`: `0.3.9`
- `spokenform`: `0.4.4.dev0+g71feb9cb4.d19800101`
- `ssmd`: `0.8.7`

The corpus includes abbreviations, units and numbers, multilingual spans,
parentheticals, multiple paragraphs, explicit breaks, markers, pronunciation
annotations, quoted sentence boundaries, punctuation, Unicode, and empty
input. The helper reports the version, revision, and dependency versions with
each run so the evidence can be refreshed without hard-coded test counts.

## Comparison policy

The helper emits normalized structural text, spoken text, preparation records,
annotations, boundaries, and frontend segments. The parity test requires exact
spoken text and compares non-whitespace segment content. It compares language
and paragraph ownership when segment counts align, normalizing language tags
such as `fr` and `fr-fr` to their base language. Provider-specific segment
splits and whitespace-only records are normalized away.

Annotation counts are compared after normalizing provider-specific annotation
kind names. Typed UtterPlan directives, resolved pauses, marker ownership, and
unit records remain UtterPlan-native consumer contract behavior.

| Behavior                      | PyKokoro representation        | UtterPlan representation                 | Policy                                                   |
| ----------------------------- | ------------------------------ | ---------------------------------------- | -------------------------------------------------------- |
| Written-to-spoken preparation | Provider preparation object    | `TextPreparationInfo` and `texts.spoken` | Compare spoken text and normalized replacements          |
| Segment text                  | Provider frontend segments     | `PlanSegment.text`                       | Compare non-whitespace content                           |
| Language                      | Provider language metadata     | `PlanSegment.language`                   | Compare base language when aligned                       |
| Coordinates                   | Provider offsets               | Spoken and structural documented ranges  | Compare normalized content and validate UtterPlan ranges |
| Pauses                        | Provider boundary handling     | `ResolvedPause` plus `BoundaryEvent`     | Keep deterministic UtterPlan semantics                   |
| Provider documents            | Request-local frontend objects | Released before plan construction        | Do not retain provider objects                           |
| Phonemes and audio            | Renderer-specific              | Not present                              | Out of scope                                             |

Run the optional suite with:

```bash
pytest -q -m reference
```

A missing sibling checkout skips the reference test. Native tests must remain
usable without PyKokoro.
