from importlib.resources import files
from pathlib import Path

from .process import run_backend


def convert_cad(source: Path, destination: Path) -> None:
    script = files("patentar_converter.scripts").joinpath("freecad_convert.py")
    run_backend(["FreeCADCmd", str(script), str(source), str(destination)])
