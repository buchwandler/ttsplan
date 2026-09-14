import pytest

from ttsplan import LanguagePlanError, build_language_runs, normalize_language


def test_normalization_and_nested_spans():
    assert normalize_language("EN_US") == "en-us"
    runs = build_language_runs(
        "abcdef", [(1, 5, "DE_DE", "explicit-span"), (2, 4, "de-de", "explicit-span")], "en-us"
    )
    assert [(x.language, x.spoken_start, x.spoken_end) for x in runs] == [
        ("en-us", 0, 1),
        ("de-de", 1, 5),
        ("en-us", 5, 6),
    ]


def test_crossing_spans_fail():
    with pytest.raises(LanguagePlanError):
        build_language_runs(
            "abcdef", [(0, 4, "de", "explicit-span"), (2, 6, "fr", "explicit-span")], "en"
        )
