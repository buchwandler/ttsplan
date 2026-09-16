from utterplan import PlannerConfig, UtterancePlanner

plan = UtterancePlanner(PlannerConfig(language="en-us")).plan("Hello.")
print([(run.language, run.spoken_start, run.spoken_end) for run in plan.languages])
