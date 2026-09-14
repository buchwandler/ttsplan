from ttsplan import PlannerConfig, TTSPlanner

plan = TTSPlanner(PlannerConfig(language="en-us", document_format="ssmd")).plan("Hello ...s world")
print(plan.to_json())
