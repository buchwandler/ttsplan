from __future__ import annotations

import json
import sys

# This helper intentionally runs only in the sibling reference subprocess.
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pykokoro"))

try:
    import pykokoro
except ImportError as exc:
    raise SystemExit(f"reference checkout unavailable: {exc}") from exc

print(json.dumps({"reference": getattr(pykokoro, "__version__", "unknown")}, sort_keys=True))
