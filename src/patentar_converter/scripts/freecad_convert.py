"""Run inside FreeCAD's Python runtime, not the package's normal interpreter."""

import sys
from pathlib import Path

import FreeCAD
import ImportGui


def main() -> None:
    source = Path(sys.argv[-2]).resolve()
    destination = Path(sys.argv[-1]).resolve()
    document = FreeCAD.newDocument("PatentARConversion")
    try:
        ImportGui.insert(str(source), document.Name)
        if not document.RootObjects:
            raise RuntimeError("FreeCAD imported no root objects")
        ImportGui.export(document.RootObjects, str(destination))
    finally:
        FreeCAD.closeDocument(document.Name)


if __name__ == "__main__":
    main()
