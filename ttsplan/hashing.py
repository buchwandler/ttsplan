from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def semantic_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def unit_hash_payload(unit: Any) -> dict[str, Any]:
    return {
        "hash_schema": "ttsplan-unit-v1",
        "segments": [
            {
                "text": segment.text,
                "language": segment.language,
                "directives": segment.directives.to_dict(),
                "pause_before": segment.pause_before.to_dict(),
                "pause_after": segment.pause_after.to_dict(),
            }
            for segment in unit.segments
        ],
        "markers": list(unit.marker_ids),
        "boundaries": [
            boundary.to_dict()
            for segment in unit.segments
            for boundary in (segment.pause_before, segment.pause_after)
        ],
    }
