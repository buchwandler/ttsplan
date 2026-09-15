# Getting started

## Install

Install the package from the distribution that matches your environment:

```bash
python -m pip install ttsplan
```

For development, install the test and documentation extras from a checkout:

```bash
python -m pip install -e '.[dev,docs]'
```

## Create a plan in Python

```python
from ttsplan import PlannerConfig, TTSPlanner

planner = TTSPlanner(PlannerConfig(language="en-us"))
plan = planner.plan("Doctor Smith bought 5 kg of apples.")

print(plan.texts.spoken)
for segment in plan.segments:
    print(segment.text, segment.language)
```

The planner produces semantic information for a renderer. It does not produce
phonemes, model tokens, or audio.

## Compile literal text

```bash
ttsplan compile "Doctor Smith bought 5 kg." --lang en-us
```

Without `-o`, the complete plan JSON is written to stdout. This makes the
result convenient for shell pipelines:

## Defaults and linguistic resources

The default compile policy is `spokenform` for text preparation, `tts` for pause mode, and `spacy off` for linguistic resources. The `spacy off` path uses TTSPlan's deterministic fallback tokenizer and analysis, so the default planner does not require an installed spaCy model.

`--spacy auto` is an explicit opt-in. With a compatible local model, it may provide richer tokenization, POS tags, lemmas, and tags. It is not the default, and TTSPlan does not download models automatically.

```bash
ttsplan compile "Hello world." --lang en-us | jq '.segments'
```

## Compile stdin or a file

```bash
echo "Hello world." | ttsplan compile --lang en-us > hello.ttsplan.json
ttsplan compile chapter.ssmd --lang en-us -o chapter.ttsplan.json
ttsplan compile --file chapter.ssmd --lang en-us -o chapter.ttsplan.json
```

A single existing positional path is read as a file. Use
`--input-format text` when a path-like value must remain literal text.

## Inspect and validate

```bash
ttsplan validate hello.ttsplan.json
ttsplan inspect hello.ttsplan.json --segment 0
ttsplan inspect hello.ttsplan.json --unit 0 --boundaries --tokens
```

## SSMD

SSMD is selected by a `.ssmd` suffix or explicitly from stdin:

```bash
printf '[Hello]{lang="en-us"} ...s [Bonjour]{lang="fr"}.\n' \
  | ttsplan compile --lang en-us --input-format ssmd
```

Structural text preserves the parsed document representation. Spoken text is
the prepared text and is the coordinate space used by segments, tokens,
markers, boundaries, and renderer-facing ranges.
