from __future__ import annotations


class UtterPlanError(Exception):
    """Base exception for UtterPlan."""


class ConfigurationError(UtterPlanError):
    """A public planning configuration value is invalid."""


class PlanFormatError(UtterPlanError):
    """The serialized plan is not structurally valid."""

    def __init__(self, message: str, *, code: str = "plan.invalid", path: str = "$") -> None:
        self.code = code
        self.path = path
        super().__init__(f"{code} at {path}: {message}")


class UnsupportedSchemaError(PlanFormatError):
    def __init__(self, version: object) -> None:
        super().__init__(
            f"Unsupported UtterPlan schema version {version}. This version of utterplan supports schema version 1.",
            code="schema.unsupported_version",
            path="$.schema_version",
        )


class PlanValidationError(PlanFormatError):
    """The plan has valid JSON shape but invalid planning semantics."""


class PlanningError(UtterPlanError):
    """Planning could not produce a plan."""


class LanguagePlanError(PlanningError):
    """Language spans cannot be resolved."""


class TextPreparationError(PlanningError):
    """Written-to-spoken preparation failed."""


class SegmentationError(PlanningError):
    """Segmentation failed."""
