import os
import unreal

# Spec 31. Run headless in UE 5.5.4. Import one FBX, scale it so its longest floor side is TARGET_CM,
# then copy the mesh to the asset path of a vanilla mesh, so a pak replaces that mesh.
# Environment: MESH_FBX, MESH_NAME, MESH_DEST (folder of the new assets), REPLACE_PATH (full object path to replace), TARGET_CM.
FBX = os.environ["MESH_FBX"]
NAME = os.environ["MESH_NAME"]
DEST = os.environ["MESH_DEST"]
REPLACE_PATH = os.environ["REPLACE_PATH"]
TARGET_CM = float(os.environ["TARGET_CM"])
BIG, SMALL = 1024, 512


def import_with_scale(scale: float):
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("import_animations", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    options.static_mesh_import_data.set_editor_property("import_uniform_scale", scale)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(DEST + "/" + NAME)
    box = mesh.get_bounding_box()
    return mesh, box.max - box.min, box


mesh, size, box = import_with_scale(1.0)
unreal.log("IMPORT first size_cm %.1f %.1f %.1f" % (size.x, size.y, size.z))
scale = TARGET_CM / max(size.x, size.y)
mesh, size, box = import_with_scale(scale)
unreal.log("IMPORT scale %.4f size_cm %.1f %.1f %.1f min_z %.1f" % (scale, size.x, size.y, size.z, box.min.z))
unreal.log("IMPORT vertices %d" % unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_number_verts(mesh, 0))
unreal.log("IMPORT materials %s" % [str(m.material_interface.get_path_name()) for m in mesh.static_materials])

for asset_path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=False):
    texture = unreal.load_asset(asset_path)
    if isinstance(texture, unreal.Texture2D):
        limit = BIG if texture.get_name() in ("texture_0", "texture_0_normal") else SMALL
        texture.set_editor_property("max_texture_size", limit)
        unreal.EditorAssetLibrary.save_loaded_asset(texture)
        unreal.log("IMPORT texture %s max %d" % (texture.get_name(), limit))

package_path = REPLACE_PATH.rsplit(".", 1)[0]
if unreal.EditorAssetLibrary.does_asset_exist(package_path):
    unreal.EditorAssetLibrary.delete_asset(package_path)
copied = unreal.EditorAssetLibrary.duplicate_asset(DEST + "/" + NAME, package_path)
unreal.log("IMPORT replace %s -> %s" % (package_path, copied))
unreal.EditorAssetLibrary.save_asset(package_path)
