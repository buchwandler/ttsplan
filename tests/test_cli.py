from ttsplan.cli import main


def test_cli_compile_validate_inspect(tmp_path, capsys):
    source = tmp_path / "source.txt"
    output = tmp_path / "source.ttsplan.json"
    source.write_text("Hello.", encoding="utf-8")
    assert main(["compile", str(source), "--language", "en-us", "-o", str(output)]) == 0
    assert main(["validate", str(output)]) == 0
    assert main(["inspect", str(output), "--segment", "0"]) == 0
    assert "valid" in capsys.readouterr().out
