from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ttsplan import PlannerConfig, TTSPlanner

from .cases import CASES


@pytest.mark.reference
def test_reference_process_is_external():
    sibling = Path(__file__).resolve().parents[3] / "pykokoro"
    if not sibling.exists():
        pytest.skip("../pykokoro is not available")
    helper = Path(__file__).with_name("dump_pykokoro_frontend.py")
    result = subprocess.run(
        [sys.executable, str(helper)], check=True, capture_output=True, text=True
    )
    assert result.stdout
    for text in CASES:
        assert TTSPlanner(PlannerConfig(language="en-us")).plan(text).texts.spoken
