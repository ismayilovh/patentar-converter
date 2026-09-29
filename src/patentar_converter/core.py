from collections.abc import Callable
from pathlib import Path

CAD_EXTENSIONS = frozenset({".iges", ".igs", ".stp", ".step"})
MESH_EXTENSIONS = frozenset({".obj", ".stl", ".fbx", ".glb", ".gltf"})
SUPPORTED_EXTENSIONS = CAD_EXTENSIONS | MESH_EXTENSIONS


class ConversionError(RuntimeError):
    """Raised when an input cannot be converted into a valid GLB."""


class UnsupportedFormatError(ConversionError):
    """Raised when the input extension is not supported."""


def _convert_mesh(source: Path, destination: Path) -> None:
    from .blender_backend import convert_mesh

    convert_mesh(source, destination)


def _convert_cad(source: Path, destination: Path) -> None:
    from .freecad_backend import convert_cad

    convert_cad(source, destination)


def validate_glb(path: Path) -> None:
    if not path.is_file():
        raise ConversionError(f"converter did not create output: {path}")
    if path.stat().st_size < 12:
        raise ConversionError(f"converter created an incomplete GLB: {path}")
    with path.open("rb") as stream:
        if stream.read(4) != b"glTF":
            raise ConversionError(f"converter output is not a binary glTF file: {path}")


def convert(
    input_path: str | Path,
    output_path: str | Path,
    *,
    mesh_converter: Callable[[Path, Path], None] = _convert_mesh,
    cad_converter: Callable[[Path, Path], None] = _convert_cad,
) -> Path:
    source = Path(input_path).expanduser().resolve()
    destination = Path(output_path).expanduser().resolve()

    if not source.is_file():
        raise ConversionError(f"input file does not exist: {source}")
    if source == destination:
        raise ConversionError("input and output paths must be different")

    extension = source.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedFormatError(
            f"unsupported input format {extension!r}; expected {supported}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)

    try:
        if extension in CAD_EXTENSIONS:
            cad_converter(source, destination)
        else:
            mesh_converter(source, destination)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"conversion backend failed: {exc}") from exc

    validate_glb(destination)
    return destination
