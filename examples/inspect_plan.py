from utterplan import UtterancePlan

plan = UtterancePlan.load("example.utterplan.json")
for segment in plan.segments:
    print(segment.text, segment.language, segment.pause_before, segment.pause_after)
