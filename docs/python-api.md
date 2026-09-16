# Python API

The supported in-process boundary is the immutable `UtterancePlan` object returned
by `UtterancePlanner`. JSON is the portable persistence and interchange format, but
an in-process consumer does not need to serialize and reload a plan.

The Python defaults are deliberately spaCy-free: `PlannerConfig` uses `spokenform` text preparation, and `PauseConfig().mode` is `"tts"`. The CLI additionally defaults to the `spacy off` linguistic-resource policy, which uses deterministic fallback tokenization and analysis without requiring an installed spaCy model.

spaCy enrichment is opt-in through the CLI's `--spacy auto` policy or an explicit `LinguisticsConfig` with a compatible local model. It may provide richer tokenization, POS tags, lemmas, and tags, but UtterPlan never downloads a model implicitly.

## Planner configuration

```{autoclass} utterplan.PlannerConfig
:members:
:show-inheritance:
```

```{autoclass} utterplan.PauseConfig
:members:
:show-inheritance:
```

```{autoclass} utterplan.LinguisticsConfig
:members:
:show-inheritance:
```

```{autoclass} utterplan.SSMDConfig
:members:
:show-inheritance:
```

## Planning and plan records

```{autoclass} utterplan.UtterancePlanner
:members:
:show-inheritance:
```

```{autoclass} utterplan.UtterancePlan
:members:
:show-inheritance:
```

```{autoclass} utterplan.PlanSegment
:members:
:show-inheritance:
```

```{autoclass} utterplan.PlanUnit
:members:
:show-inheritance:
```

The public model also exposes `languages`, `annotations`, `boundaries`,
`tokens`, `markers`, `document_metadata`, and resolved segment pauses. See the
[consumer guide](consumer-guide) for how a renderer uses these fields.

`TextPreparationInfo` exposes serializable provenance only. Exact source-to-spoken mapping is transient planner state and is not part of `UtterancePlan` or its JSON contract.

## Errors

Planning and loading failures derive from `utterplan.UtterPlanError`. Important
public subclasses include `ConfigurationError`, `PlanningError`,
`PlanFormatError`, `PlanValidationError`, and `UnsupportedSchemaError`.
