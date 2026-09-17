from __future__ import annotations

FORMAT = "utterplan"
CURRENT_SCHEMA_VERSION = 1
OLDEST_SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS: tuple[int, ...] = (1,)

# Compatibility alias retained for existing callers.
SCHEMA_VERSION = CURRENT_SCHEMA_VERSION
