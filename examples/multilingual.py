from ttsplan import PlannerConfig, TTSPlanner

plan = TTSPlanner(PlannerConfig(language="en-us")).plan("Hello.")
print([(run.language, run.spoken_start, run.spoken_end) for run in plan.languages])
