import bpy
import os

#empty scene to prevent loading old stuff.
def empty_blender_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

#converts .obj files to .glb.
def convert_obj(file_path, output_path):
    empty_blender_scene()
    bpy.ops.wm.obj_import(filepath=file_path)
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')

#converts .fbx files to .glb.
def convert_fbx(file_path, output_path):
    empty_blender_scene()
    bpy.ops.wm.fbx_import(filepath=file_path)
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB', export_materials='EXPORT')

#converts .stl files to .glb.
def convert_stl(file_path, output_path):
    empty_blender_scene()
    bpy.ops.wm.stl_import(filepath=file_path)
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB', export_materials='EXPORT')

def convert_non_cad(file_path, file_type):

    output_path = os.environ.get("OUTPUT_PATH")
    if file_type == ".obj":
        convert_obj(file_path, output_path)
    elif file_type == ".fbx":
        convert_fbx(file_path, output_path)
    elif file_type == ".stl":
        convert_stl(file_path, output_path)
    else:
        print("Error: Unsupported 3D model type!")
