from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# This helper intentionally imports PyKokoro only in its subprocess.
ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "pykokoro"
sys.path.insert(0, str(REFERENCE))

try:
    import pykokoro
    from pykokoro import GenerationConfig, KokoroPipeline, PipelineConfig
    from pykokoro.tokenizer import TokenizerConfig
except ImportError as exc:
    raise SystemExit(f"reference checkout unavailable: {exc}") from exc


def _revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REFERENCE), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _value(item: object, *names: str, default: object = None) -> object:
    for name in names:
        if hasattr(item, name):
            return getattr(item, name)
    return default


def normalize(text: str) -> dict[str, object]:
    pipeline = KokoroPipeline(
        PipelineConfig(
            generation=GenerationConfig(lang="en-us"),
            tokenizer_config=TokenizerConfig(use_spacy=False),
            allow_experimental_frontend=True,
        )
    )
    frontend = pipeline.prepare_frontend(text)
    try:
        document = frontend._doc
        segments = [
            {
                "text": str(_value(item, "text", default="")),
                "spoken_start": int(_value(item, "char_start", "start", default=0)),
                "spoken_end": int(_value(item, "char_end", "end", default=0)),
                "language": str(_value(item, "meta", default={}).get("language", "en-us")),
                "paragraph": int(_value(item, "paragraph_idx", default=0) or 0),
                "sentence": int(_value(item, "sentence_idx", default=0) or 0),
                "clause": int(_value(item, "clause_idx", default=0) or 0),
            }
            for item in getattr(document, "segments", ())
        ]
        annotations = [
            {
                "structural_start": int(_value(item, "char_start", "start", default=0)),
                "structural_end": int(_value(item, "char_end", "end", default=0)),
                "kind": str(_value(item, "kind", default="annotation")),
                "attrs": dict(_value(item, "attrs", default={})),
            }
            for item in getattr(document, "annotation_spans", ())
        ]
        boundaries = [
            {
                "position": int(_value(item, "pos", "position", default=0)),
                "kind": str(_value(item, "kind", default="unknown")),
                "seconds": _value(item, "duration_s", "seconds"),
                "attrs": dict(_value(item, "attrs", default={})),
            }
            for item in getattr(document, "boundary_events", ())
        ]
        preparation = getattr(document, "preparation", None)
        return {
            "structural_text": str(
                _value(document, "structural_clean_text", "clean_text", default="")
            ),
            "spoken_text": str(_value(preparation, "spoken_text", default="")),
            "languages": [],
            "annotations": annotations,
            "tokens": [],
            "segments": segments,
            "boundaries": boundaries,
            "markers": [],
            "preparation": {
                "replacements": list(_value(preparation, "replacements", default=()) or ()),
                "warnings": list(_value(preparation, "warnings", default=()) or ()),
            },
        }
    finally:
        frontend.close()


def main() -> None:
    raw = sys.stdin.read().strip()
    if raw:
        values = json.loads(raw)
        cases = values if isinstance(values, list) else [str(values)]
    else:
        cases = ["Doctor Smith bought 5 kg.", "Hello ...s world", 'Hello [Bonjour]{lang="fr"}.']
    output = {
        "reference": getattr(pykokoro, "__version__", "unknown"),
        "commit": _revision(),
        "cases": [{"input": text, "frontend": normalize(str(text))} for text in cases],
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
