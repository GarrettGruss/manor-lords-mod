import os
import unreal

NAME = os.environ.get("BM_NAME", "BM_HarnessCamp")
PATH = os.environ.get("BM_PATH", "/Game/HarnessMod")
# The game classifies the parts of a BM class by the name prefix of each component (MainBld_, Bld_, clutter_, res_).
PART_NAMES = ["MainBld_900", "MainBld_901", "Bld_902"]
MESHES = [
    ("/Engine/BasicShapes/Cube.Cube", (0, 0, 100), (4.0, 4.0, 2.0)),
    ("/Engine/BasicShapes/Cone.Cone", (500, 0, 150), (3.0, 3.0, 3.0)),
    ("/Engine/BasicShapes/Sphere.Sphere", (-500, 0, 150), (3.0, 3.0, 3.0)),
]

tools = unreal.AssetToolsHelpers.get_asset_tools()
if unreal.EditorAssetLibrary.does_asset_exist(PATH + "/" + NAME):
    unreal.EditorAssetLibrary.delete_asset(PATH + "/" + NAME)
factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.StaticMeshActor)
bp = tools.create_asset(NAME, PATH, unreal.Blueprint, factory)
unreal.log("BM created %s" % bp)

sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sub.k2_gather_subobject_data_for_blueprint(bp)
root = handles[0]
for index, (mesh_path, loc, scale) in enumerate(MESHES):
    params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)
    handle, fail = sub.add_new_subobject(params)
    unreal.log("BM add %d fail=%s" % (index, fail))
    sub.rename_subobject(handle, PART_NAMES[index])
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    comp.set_editor_property("static_mesh", unreal.load_asset(mesh_path))
    comp.set_editor_property("relative_location", unreal.Vector(*loc))
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(PATH + "/" + NAME)
unreal.log("BM done")
