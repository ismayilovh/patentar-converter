from pathlib import Path

from patentar_converter import cli


def test_cli_requires_glb_output(input_file: Path, tmp_path: Path, capsys) -> None:
    result = cli.main([str(input_file), "--output", str(tmp_path / "model.obj")])

    assert result == 2
    assert "must end with .glb" in capsys.readouterr().err


def test_cli_reports_conversion_error(
    monkeypatch, input_file: Path, tmp_path: Path, capsys
) -> None:
    def fail(*_args, **_kwargs):
        raise cli.ConversionError("backend unavailable")

    monkeypatch.setattr(cli, "convert", fail)

    result = cli.main([str(input_file), "--output", str(tmp_path / "model.glb")])

    assert result == 1
    assert "backend unavailable" in capsys.readouterr().err
