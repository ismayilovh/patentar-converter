from importlib.resources import files
from pathlib import Path

from .process import run_backend


def convert_mesh(source: Path, destination: Path) -> None:
    script = files("patentar_converter.scripts").joinpath("blender_convert.py")
    run_backend(
        [
            "blender",
            "--background",
            "--factory-startup",
            "--python",
            str(script),
            "--",
            str(source),
            str(destination),
        ]
    )
