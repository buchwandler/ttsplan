from pathlib import Path

from utterplan import PlannerConfig, UtterancePlanner

source = Path("chapter.ssmd").read_text(encoding="utf-8")
plan = UtterancePlanner(PlannerConfig(language="en-us", document_format="ssmd")).plan(source)
plan.save("chapter.utterplan.json")
