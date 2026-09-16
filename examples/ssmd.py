from utterplan import PlannerConfig, UtterancePlanner

plan = UtterancePlanner(PlannerConfig(language="en-us", document_format="ssmd")).plan(
    "Hello ...s world"
)
print(plan.to_json())
