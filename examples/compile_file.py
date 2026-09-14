from pathlib import Path

from ttsplan import PlannerConfig, TTSPlanner

source = Path("chapter.ssmd").read_text(encoding="utf-8")
plan = TTSPlanner(PlannerConfig(language="en-us", document_format="ssmd")).plan(source)
plan.save("chapter.ttsplan.json")
