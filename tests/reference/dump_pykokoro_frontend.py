from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from dataclasses import asdict, is_dataclass
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


def _versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in ("phrasplit", "spokenform", "ssmd"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "unknown"
    return versions


def _plain(value: object) -> object:
    if is_dataclass(value):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _value(item: object, *names: str, default: object = None) -> object:
    for name in names:
        if hasattr(item, name):
            return getattr(item, name)
    return default


def _language_runs(frontend: object) -> list[dict[str, object]]:
    state = object.__getattribute__(frontend, "_state")
    runs = getattr(state, "prepared_plan", ())
    return [
        {
            "spoken_start": int(_value(run, "char_start", "start", default=0)),
            "spoken_end": int(_value(run, "char_end", "end", default=0)),
            "language": str(_value(run, "language", default="")),
        }
        for run in runs
    ]


def _annotations(document: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for index, item in enumerate(getattr(document, "annotation_spans", ())):
        result.append(
            {
                "id": f"annotation-{index:06d}",
                "spoken_start": int(_value(item, "char_start", "start", default=0)),
                "spoken_end": int(_value(item, "char_end", "end", default=0)),
                "kind": str(_value(item, "kind", default="annotation")),
                "attrs": dict(_plain(_value(item, "attrs", default={}))),
            }
        )
    return result


def _tokens(frontend: object) -> list[dict[str, object]]:
    state = object.__getattribute__(frontend, "_state")
    result: list[dict[str, object]] = []
    for analysis in getattr(state, "prepared_analysis", ()):
        for token in getattr(analysis, "annotations", ()):
            result.append(
                {
                    "spoken_start": int(_value(token, "start", default=0)),
                    "spoken_end": int(_value(token, "end", default=0)),
                    "text": str(_value(token, "text", default="")),
                    "pos": _value(token, "pos"),
                    "tag": _value(token, "tag"),
                    "lemma": _value(token, "lemma"),
                    "language": _value(token, "language"),
                }
            )
    return result


def _segments(document: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    sentence = 0
    paragraph = 0
    for item in getattr(document, "segments", ()):
        text = str(_value(item, "text", default=""))
        if not text.strip():
            continue
        current_paragraph = int(_value(item, "paragraph_idx", default=0) or 0)
        if result and current_paragraph != paragraph:
            paragraph = current_paragraph
            sentence = 0
        elif (
            result
            and result[-1]["text"].rstrip("\"'»”’)]}").endswith((".", "!", "?"))
            and int(_value(item, "char_start", "start", default=0)) > int(result[-1]["spoken_end"])
        ):
            sentence += 1
        result.append(
            {
                "text": text,
                "spoken_start": int(_value(item, "char_start", "start", default=0)),
                "spoken_end": int(_value(item, "char_end", "end", default=0)),
                "language": str(_value(item, "meta", default={}).get("language", "")),
                "paragraph": paragraph,
                "sentence": sentence,
                "clause": int(_value(item, "clause_idx", default=0) or 0),
            }
        )
    return result


def _boundaries(document: object) -> list[dict[str, object]]:
    return [
        {
            "position": int(_value(item, "pos", "position", default=0)),
            "kind": str(_value(item, "kind", default="unknown")),
            "seconds": _value(item, "duration_s", "seconds"),
            "attrs": dict(_plain(_value(item, "attrs", default={}))),
        }
        for item in getattr(document, "boundary_events", ())
    ]


def _units(
    segments: list[dict[str, object]], boundaries: list[dict[str, object]], kind: str
) -> list[dict[str, object]]:
    groups: list[list[dict[str, object]]] = []
    keys: list[tuple[object, ...]] = []
    for segment in segments:
        key = (
            (
                "paragraph",
                segment["paragraph"],
            )
            if kind == "paragraph"
            else ("sentence", segment["paragraph"], segment["sentence"])
        )
        if not groups or keys[-1] != key:
            keys.append(key)
            groups.append([])
        groups[-1].append(segment)
    result: list[dict[str, object]] = []
    for index, group in enumerate(groups):
        start = int(group[0]["spoken_start"])
        end = int(group[-1]["spoken_end"])
        marker_positions = {
            int(boundary["position"])
            for boundary in boundaries
            if boundary["kind"] == "marker" and start <= int(boundary["position"]) <= end
        }
        result.append(
            {
                "index": index,
                "kind": kind,
                "spoken_start": start,
                "spoken_end": end,
                "segment_indices": list(
                    range(
                        sum(len(item) for item in groups[:index]),
                        sum(len(item) for item in groups[: index + 1]),
                    )
                ),
                "marker_positions": sorted(marker_positions),
            }
        )
    return result


def normalize(text: str, *, unit: str = "paragraph") -> dict[str, object]:
    pipeline = KokoroPipeline(
        PipelineConfig(
            generation=GenerationConfig(lang="en-us"),
            tokenizer_config=TokenizerConfig(use_spacy=False),
            allow_experimental_frontend=True,
        )
    )
    frontend = pipeline.prepare_frontend(text, unit=unit)
    try:
        document = frontend._doc
        segments = _segments(document)
        boundaries = _boundaries(document)
        preparation = getattr(document, "preparation", None)
        return {
            "structural_text": str(
                _value(document, "structural_clean_text", "clean_text", default="")
            ),
            "spoken_text": str(_value(preparation, "spoken_text", default="")),
            "languages": _language_runs(frontend),
            "annotations": _annotations(document),
            "tokens": _tokens(frontend),
            "segments": segments,
            "boundaries": boundaries,
            "markers": [
                {
                    "name": str(boundary["attrs"].get("name", boundary["attrs"].get("marker", ""))),
                    "spoken_position": boundary["position"],
                    "attrs": boundary["attrs"],
                }
                for boundary in boundaries
                if boundary["kind"] == "marker"
            ],
            "units": _units(segments, boundaries, unit),
            "preparation": {
                "replacements": list(_plain(_value(preparation, "replacements", default=())) or ()),
                "warnings": list(_plain(_value(preparation, "warnings", default=())) or ()),
            },
            "document_metadata": {
                "header": dict(_plain(getattr(document, "header", {}))),
                "metadata": dict(_plain(getattr(document, "metadata", {}))),
            },
        }
    finally:
        frontend.close()
        pipeline.close()


def main() -> None:
    raw = sys.stdin.read().strip()
    if raw:
        values = json.loads(raw)
        cases = values if isinstance(values, list) else [str(values)]
    else:
        cases = ["Doctor Smith bought 5 kg.", "Hello ...s world"]
    output = {
        "reference": getattr(pykokoro, "__version__", "unknown"),
        "commit": _revision(),
        "dependency_versions": _versions(),
        "cases": [
            {
                "input": text,
                "frontend": normalize(str(text)),
            }
            for text in cases
        ],
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
