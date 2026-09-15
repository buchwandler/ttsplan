from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ttsplan import PlannerConfig, TTSPlanner

from .cases import CASES


@pytest.mark.reference
def test_reference_frontend_normalized_parity() -> None:
    sibling = Path(__file__).resolve().parents[3] / "pykokoro"
    if not sibling.exists():
        pytest.skip("../pykokoro is not available")
    helper = Path(__file__).with_name("dump_pykokoro_frontend.py")
    result = subprocess.run(
        [sys.executable, str(helper)],
        input=json.dumps(list(CASES)),
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["reference"]
    assert payload["commit"]
    assert set(payload["dependency_versions"]) == {"phrasplit", "spokenform", "ssmd"}

    for case in payload["cases"]:
        plan = TTSPlanner(PlannerConfig(language="en-us")).plan(case["input"])
        reference = case["frontend"]
        assert reference["spoken_text"] == plan.texts.spoken

        reference_segments = [
            segment for segment in reference["segments"] if segment["text"].strip()
        ]
        native_segments = [
            {
                "text": segment.text,
                "language": segment.language,
                "paragraph": segment.paragraph,
                "sentence": segment.sentence,
                "clause": segment.clause,
            }
            for segment in plan.segments
        ]

        def normalize(value: str) -> str:
            return "".join(value.split())

        reference_content = "".join(segment["text"] for segment in reference_segments)
        native_content = "".join(segment["text"] for segment in native_segments)
        assert normalize(reference_content) == normalize(native_content)

        if len(reference_segments) == len(native_segments):

            def base_language(value: str) -> str:
                return value.split("-", 1)[0]

            assert [base_language(segment["language"]) for segment in reference_segments] == [
                base_language(segment["language"]) for segment in native_segments
            ]
            assert [segment["paragraph"] for segment in reference_segments] == [
                segment["paragraph"] for segment in native_segments
            ]

        # The reference frontend exposes generic annotation records; compare
        # normalized cardinality rather than provider-specific kind names.
        assert len(reference["annotations"]) == len(plan.annotations)
