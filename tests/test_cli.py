from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from ttsplan.cli import main


def _payload(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


def test_compile_literal_text_to_stdout_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compile", "Hello world.", "--lang", "en-us"]) == 0
    payload = _payload(capsys)
    assert payload["format"] == "ttsplan"
    assert payload["schema_version"] == 1
    assert payload["segments"]


def test_compile_multi_token_literal_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compile", "Hello", "world.", "--lang", "en-us"]) == 0
    payload = _payload(capsys)
    assert payload["source"]["text"] == "Hello world."


def test_compile_reads_stdin_when_text_is_omitted(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("Hello from stdin."))
    assert main(["compile", "--lang", "en-us"]) == 0
    assert _payload(capsys)["source"]["text"] == "Hello from stdin."


def test_compile_positional_existing_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Hello from a file.", encoding="utf-8")
    assert main(["compile", str(source), "--lang", "en-us"]) == 0
    payload = _payload(capsys)
    assert payload["source"]["text"] == "Hello from a file."
    assert payload["source"]["format"] == "plain"


def test_compile_explicit_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Explicit file input.", encoding="utf-8")
    assert main(["compile", "--file", str(source), "--lang", "en-us"]) == 0
    assert _payload(capsys)["source"]["text"] == "Explicit file input."


def test_compile_explicit_text_disables_file_detection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "literal.txt"
    source.write_text("file contents", encoding="utf-8")
    assert main(["compile", str(source), "--input-format", "text", "--lang", "en-us"]) == 0
    assert _payload(capsys)["source"]["text"] == str(source)


def test_compile_auto_detects_ssmd_suffix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "chapter.ssmd"
    source.write_text("Hello SSMD.", encoding="utf-8")
    assert main(["compile", str(source), "--lang", "en-us"]) == 0
    assert _payload(capsys)["source"]["format"] == "ssmd"


def test_compile_explicit_ssmd_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("Hello SSMD."))
    assert main(["compile", "--lang", "en-us", "--input-format", "ssmd"]) == 0
    assert _payload(capsys)["source"]["format"] == "ssmd"


def test_compile_output_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "plan.ttsplan.json"
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "wrote" in captured.err
    assert json.loads(output.read_text(encoding="utf-8"))["format"] == "ttsplan"


def test_compile_output_file_and_json_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "plan.ttsplan.json"
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output), "--json"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == json.loads(output.read_text(encoding="utf-8"))


def test_compile_refuses_existing_output_without_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "plan.ttsplan.json"
    output.write_text("sentinel", encoding="utf-8")
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output)]) == 1
    captured = capsys.readouterr()
    assert "--force" in captured.err
    assert output.read_text(encoding="utf-8") == "sentinel"


def test_compile_force_replaces_existing_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "plan.ttsplan.json"
    output.write_text("sentinel", encoding="utf-8")
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output), "--force"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "wrote" in captured.err
    assert json.loads(output.read_text(encoding="utf-8"))["format"] == "ttsplan"


def test_compile_json_stdout_contains_no_status_text(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compile", "Hello.", "--lang", "en-us", "--json"]) == 0
    captured = capsys.readouterr()
    assert "wrote" not in captured.out
    json.loads(captured.out)


def test_compile_status_goes_to_stderr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "plan.ttsplan.json"
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("wrote ")


def test_compile_invalid_ssmd_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "broken.ssmd"
    source.write_text("---\npause_defaults: [\n---\nHello.", encoding="utf-8")
    assert main(["compile", str(source), "--lang", "en-us"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Traceback" not in captured.err


def test_top_level_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as result:
        main(["--version"])
    assert result.value.code == 0
    assert capsys.readouterr().out.startswith("ttsplan ")


def test_validate_valid_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "plan.ttsplan.json"
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output)]) == 0
    capsys.readouterr()
    assert main(["validate", str(output)]) == 0
    assert "valid" in capsys.readouterr().out


def test_validate_invalid_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert main(["validate", str(invalid)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "format.invalid" in captured.err


def test_inspect_segment(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "plan.ttsplan.json"
    assert main(["compile", "Hello.", "--lang", "en-us", "-o", str(output)]) == 0
    capsys.readouterr()
    assert main(["inspect", str(output), "--segment", "0"]) == 0
    captured = capsys.readouterr()
    assert "Segment 0" in captured.out
    assert "Hello" in captured.out


def test_compile_file_and_positional_text_are_mutually_exclusive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Hello.", encoding="utf-8")
    assert main(["compile", "extra", "--file", str(source), "--lang", "en-us"]) == 1
    assert "cannot be combined" in capsys.readouterr().err
