from pathlib import Path

import pytest

from patentar_converter.core import ConversionError, UnsupportedFormatError, convert


def test_dispatches_mesh_conversion(input_file: Path, glb_bytes: bytes, tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "model.glb"
    calls: list[tuple[Path, Path]] = []

    def mesh_converter(source: Path, output: Path) -> None:
        calls.append((source, output))
        output.write_bytes(glb_bytes)

    result = convert(input_file, destination, mesh_converter=mesh_converter)

    assert result == destination.resolve()
    assert calls == [(input_file.resolve(), destination.resolve())]


def test_dispatches_cad_conversion(tmp_path: Path, glb_bytes: bytes) -> None:
    source = tmp_path / "part.step"
    destination = tmp_path / "part.glb"
    source.write_bytes(b"STEP")

    def cad_converter(_: Path, output: Path) -> None:
        output.write_bytes(glb_bytes)

    convert(source, destination, cad_converter=cad_converter)
    assert destination.read_bytes() == glb_bytes


def test_rejects_unsupported_format(tmp_path: Path) -> None:
    source = tmp_path / "model.zip"
    source.write_bytes(b"zip")

    with pytest.raises(UnsupportedFormatError, match="unsupported input format"):
        convert(source, tmp_path / "model.glb")


def test_rejects_missing_or_invalid_output(input_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ConversionError, match="did not create output"):
        convert(input_file, tmp_path / "missing.glb", mesh_converter=lambda *_: None)

    def invalid_converter(_: Path, output: Path) -> None:
        output.write_bytes(b"not a glb file")

    with pytest.raises(ConversionError, match="not a binary glTF"):
        convert(input_file, tmp_path / "invalid.glb", mesh_converter=invalid_converter)


def test_rejects_same_input_and_output(input_file: Path) -> None:
    with pytest.raises(ConversionError, match="must be different"):
        convert(input_file, input_file)
