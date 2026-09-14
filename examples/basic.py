from ttsplan import PlannerConfig, TTSPlanner

plan = TTSPlanner(PlannerConfig(language="en-us", document_format="plain")).plan(
    "Doctor Smith bought 5 kg of apples."
)
plan.save("example.ttsplan.json")
print(plan.plan_id)
