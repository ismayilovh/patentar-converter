"""Run inside Blender's Python runtime, not the package's normal interpreter."""

import sys
from pathlib import Path

import bpy


def main() -> None:
    separator = sys.argv.index("--")
    source = Path(sys.argv[separator + 1]).resolve()
    destination = Path(sys.argv[separator + 2]).resolve()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    extension = source.suffix.lower()

    if extension == ".obj":
        bpy.ops.wm.obj_import(filepath=str(source))
    elif extension == ".stl":
        bpy.ops.wm.stl_import(filepath=str(source))
    elif extension == ".fbx":
        bpy.ops.wm.fbx_import(filepath=str(source))
    elif extension in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(source))
    else:
        raise ValueError(f"unsupported Blender input format: {extension}")

    bpy.ops.export_scene.gltf(
        filepath=str(destination),
        export_format="GLB",
        export_materials="EXPORT",
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )


if __name__ == "__main__":
    main()
