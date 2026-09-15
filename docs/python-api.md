# Python API

The supported in-process boundary is the immutable `TTSPlan` object returned
by `TTSPlanner`. JSON is the portable persistence and interchange format, but
an in-process consumer does not need to serialize and reload a plan.

## Planner configuration

```{autoclass} ttsplan.PlannerConfig
:members:
:show-inheritance:
```

```{autoclass} ttsplan.PauseConfig
:members:
:show-inheritance:
```

```{autoclass} ttsplan.LinguisticsConfig
:members:
:show-inheritance:
```

```{autoclass} ttsplan.SSMDConfig
:members:
:show-inheritance:
```

## Planning and plan records

```{autoclass} ttsplan.TTSPlanner
:members:
:show-inheritance:
```

```{autoclass} ttsplan.TTSPlan
:members:
:show-inheritance:
```

```{autoclass} ttsplan.PlanSegment
:members:
:show-inheritance:
```

```{autoclass} ttsplan.PlanUnit
:members:
:show-inheritance:
```

The public model also exposes `languages`, `annotations`, `boundaries`,
`tokens`, `markers`, `document_metadata`, and resolved segment pauses. See the
[consumer guide](consumer-guide) for how a renderer uses these fields.

## Errors

Planning and loading failures derive from `ttsplan.TTSPlanError`. Important
public subclasses include `ConfigurationError`, `PlanningError`,
`PlanFormatError`, `PlanValidationError`, and `UnsupportedSchemaError`.
