from utterplan import PlannerConfig, UtterancePlanner

plan = UtterancePlanner(PlannerConfig(language="en-us", document_format="plain")).plan(
    "Doctor Smith bought 5 kg of apples."
)
plan.save("example.utterplan.json")
print(plan.plan_id)
