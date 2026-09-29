from pathlib import Path

import pytest


@pytest.fixture
def glb_bytes() -> bytes:
    return b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little")


@pytest.fixture
def input_file(tmp_path: Path) -> Path:
    source = tmp_path / "model.obj"
    source.write_text("o test\n", encoding="utf-8")
    return source
