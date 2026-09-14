from ttsplan import TTSPlan

plan = TTSPlan.load("example.ttsplan.json")
for segment in plan.segments:
    print(segment.text, segment.language, segment.pause_before, segment.pause_after)
