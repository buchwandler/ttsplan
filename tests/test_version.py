from __future__ import annotations

from importlib.metadata import version

from packaging.version import Version

import ttsplan


def test_public_version_matches_package_metadata() -> None:
    assert version("ttsplan") == ttsplan.__version__


def test_version_is_pep440() -> None:
    Version(ttsplan.__version__)
