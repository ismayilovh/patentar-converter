# PatentAR Converter

PatentAR Converter normalizes supported CAD and mesh files into GLB files for the PatentAR model pipeline. It contains no web API, database schema, user accounts, or GPU inference code.

## Supported input formats

- CAD: `.step`, `.stp`, `.iges`, `.igs`
- Mesh: `.obj`, `.stl`, `.fbx`, `.glb`, `.gltf`

Blender handles mesh formats and GLB normalization. FreeCAD handles CAD inputs. Generated GLB files are checked for the binary glTF header before the command succeeds.

## Command-line contract

```text
patentar-convert INPUT --output OUTPUT
```

Example:

```bash
patentar-convert /work/input/model.step --output /work/output/model.glb
```

The output path is explicit and never inferred from the current directory. A successful conversion exits with code `0`; invalid input, unsupported formats, backend errors, missing output, or invalid GLB output return a non-zero code.

## Container

```bash
docker build -t patentar-converter:local .
docker run --rm \
  --mount type=bind,src="$PWD/work",dst=/work \
  patentar-converter:local \
  /work/input/model.step --output /work/output/model.glb
```

Versioned images are published to GitHub Container Registry. The model worker should pin a release digest rather than use `latest`.

## Development

The unit tests do not import Blender or FreeCAD; backend imports are lazy so the orchestration contract can be tested in a normal Python environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ruff check .
pytest
```
