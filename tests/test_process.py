import subprocess

import pytest

from patentar_converter.process import run_backend


def test_backend_reports_nonzero_exit(monkeypatch) -> None:
    completed = subprocess.CompletedProcess(["blender"], 2, stdout="", stderr="bad mesh")
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: completed)

    with pytest.raises(RuntimeError, match="bad mesh"):
        run_backend(["blender"])


def test_backend_reports_missing_executable(monkeypatch) -> None:
    def missing(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)

    with pytest.raises(RuntimeError, match="unavailable"):
        run_backend(["FreeCADCmd"])
