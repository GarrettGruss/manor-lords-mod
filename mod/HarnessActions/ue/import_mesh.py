import os
import unreal

# Run headless in UE 5.5.4. Imports one FBX with its textures and material,
# then logs the bounds (cm) and triangle count so the size can be checked.
FBX = os.environ["MESH_FBX"]
DEST = os.environ.get("MESH_DEST", "/Game/HarnessMod/Meshes")
NAME = os.environ["MESH_NAME"]

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_as_skeletal", False)
options.set_editor_property("import_materials", True)
options.set_editor_property("import_textures", True)
options.set_editor_property("import_animations", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
options.static_mesh_import_data.set_editor_property("import_uniform_scale", float(os.environ.get("MESH_SCALE", "1.0")))

task = unreal.AssetImportTask()
task.set_editor_property("filename", FBX)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.log("IMPORT paths %s" % list(task.get_editor_property("imported_object_paths")))

mesh = unreal.load_asset(DEST + "/" + NAME)
box = mesh.get_bounding_box()
size = box.max - box.min
unreal.log("IMPORT size_cm %.1f %.1f %.1f min_z %.1f" % (size.x, size.y, size.z, box.min.z))
unreal.log("IMPORT vertices %d" % unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_number_verts(mesh, 0))
unreal.log("IMPORT materials %s" % [str(m.material_interface.get_path_name()) for m in mesh.static_materials])

# Keep the pak small: cap each texture. Base colour and normal 1024, the others 512 (set MESH_TEX_BIG / MESH_TEX_SMALL to change).
BIG = int(os.environ.get("MESH_TEX_BIG", "1024"))
SMALL = int(os.environ.get("MESH_TEX_SMALL", "512"))
for asset_path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=False):
    texture = unreal.load_asset(asset_path)
    if not isinstance(texture, unreal.Texture2D):
        continue
    name = texture.get_name()
    limit = BIG if name in ("texture_0", "texture_0_normal") else SMALL
    texture.set_editor_property("max_texture_size", limit)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    unreal.log("IMPORT texture %s max %d" % (name, limit))
