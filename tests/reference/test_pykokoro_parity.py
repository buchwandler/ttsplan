from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from utterplan import PlannerConfig, UtterancePlanner

from .cases import CASES


def _portable_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in attrs.items()
        if key not in {"voice_name", "voice_reference", "voice_source"}
    }


def _plan_projection(plan: Any) -> dict[str, Any]:
    return {
        "spoken_text": plan.texts.spoken,
        "languages": [
            {
                "spoken_start": run.spoken_start,
                "spoken_end": run.spoken_end,
                "language": run.language,
            }
            for run in plan.languages
        ],
        "annotations": [
            {
                "spoken_start": annotation.spoken_start,
                "spoken_end": annotation.spoken_end,
                "attrs": _portable_attrs(dict(annotation.attrs)),
            }
            for annotation in plan.annotations
        ],
        "segments": [
            {
                "text": segment.text,
                "spoken_start": segment.spoken_start,
                "spoken_end": segment.spoken_end,
                "language": segment.language,
                "paragraph": segment.paragraph,
                "sentence": segment.sentence,
                "clause": segment.clause,
            }
            for segment in plan.segments
        ],
        "boundaries": [
            {
                "position": boundary.position,
                "kind": boundary.kind,
                "seconds": boundary.seconds
                if boundary.seconds is not None
                else next(
                    (
                        segment.pause_after.seconds
                        if segment.spoken_end == boundary.position
                        else segment.pause_before.seconds
                        for segment in plan.segments
                        if segment.spoken_end == boundary.position
                        or segment.spoken_start == boundary.position
                    ),
                    0.0,
                ),
                "attrs": dict(boundary.attrs),
            }
            for boundary in plan.boundaries
        ],
        "markers": [
            {
                "name": marker.name,
                "spoken_position": marker.spoken_position,
                "attrs": dict(marker.attrs),
            }
            for marker in plan.markers
        ],
        "units": [
            {
                "kind": unit.kind,
                "spoken_start": unit.spoken_start,
                "spoken_end": unit.spoken_end,
                "segment_indices": [
                    plan.segments.index(
                        next(segment for segment in plan.segments if segment.id == segment_id)
                    )
                    for segment_id in unit.segment_ids
                ],
            }
            for unit in plan.units
        ],
    }


def _reference_projection(reference: dict[str, Any]) -> dict[str, Any]:
    boundaries = []
    valid_positions = {int(segment["spoken_start"]) for segment in reference["segments"]} | {
        int(segment["spoken_end"]) for segment in reference["segments"]
    }
    for boundary in reference["boundaries"]:
        if boundary["kind"] == "marker" or boundary["position"] not in valid_positions:
            continue
        strength = boundary["attrs"].get("strength")
        kind = "paragraph" if strength == "p" else "explicit"
        candidate = {
            "position": boundary["position"],
            "kind": kind,
            "seconds": boundary["seconds"],
            "attrs": {
                **boundary["attrs"],
                "source": "planner_default"
                if boundary["attrs"].get("source") == "pipeline_default"
                else boundary["attrs"].get("source"),
            },
        }
        if not any(
            item["position"] == candidate["position"] and item["kind"] == candidate["kind"]
            for item in boundaries
        ):
            boundaries.append(candidate)
    languages = [dict(run) for run in reference["languages"]]
    for run in languages:
        run["language"] = (
            str(run["language"]).split("-", 1)[0]
            if str(run["language"]).startswith("fr-")
            else run["language"]
        )
    segments = [dict(segment) for segment in reference["segments"]]
    for segment in segments:
        segment["language"] = (
            str(segment["language"]).split("-", 1)[0]
            if str(segment["language"]).startswith("fr-")
            else segment["language"]
        )
    return {
        "spoken_text": reference["spoken_text"],
        "languages": languages,
        "annotations": [
            {
                "spoken_start": annotation["spoken_start"],
                "spoken_end": annotation["spoken_end"],
                "attrs": _portable_attrs(annotation["attrs"]),
            }
            for annotation in reference["annotations"]
        ],
        "segments": segments,
        "boundaries": boundaries,
        "markers": [
            {
                "name": marker["name"],
                "spoken_position": marker["spoken_position"],
                "attrs": {"name": marker["name"]},
            }
            for marker in reference["markers"]
        ],
        "units": [
            {
                "kind": unit["kind"],
                "spoken_start": unit["spoken_start"],
                "spoken_end": unit["spoken_end"],
                "segment_indices": unit["segment_indices"],
            }
            for unit in reference["units"]
        ],
    }


@pytest.mark.reference
def test_reference_frontend_strict_migration_parity() -> None:
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
        plan = UtterancePlanner(PlannerConfig(language="en-us")).plan(case["input"])
        reference = _reference_projection(case["frontend"])
        actual = _plan_projection(plan)

        assert actual["spoken_text"] == reference["spoken_text"]
        assert actual["languages"] == reference["languages"]
        assert actual["annotations"] == reference["annotations"]
        assert actual["segments"] == reference["segments"]
        assert actual["markers"] == reference["markers"]
        assert actual["units"] == reference["units"]

        for expected in reference["boundaries"]:
            matches = [
                boundary
                for boundary in actual["boundaries"]
                if boundary["position"] == expected["position"]
                and boundary["kind"] == expected["kind"]
            ]
            assert matches
            assert any(
                boundary["seconds"] == expected["seconds"]
                and all(
                    boundary["attrs"].get(key) == value for key, value in expected["attrs"].items()
                )
                for boundary in matches
            )

        if case["frontend"]["tokens"]:
            assert [
                {
                    "spoken_start": token.spoken_start,
                    "spoken_end": token.spoken_end,
                    "text": token.text,
                    "pos": token.pos,
                    "tag": token.tag,
                    "lemma": token.lemma,
                    "language": token.language,
                }
                for token in plan.tokens
            ] == case["frontend"]["tokens"]
