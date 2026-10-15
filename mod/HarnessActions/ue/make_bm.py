import json
import os
import unreal

NAME = os.environ.get("BM_NAME", "BM_HarnessCamp")
PATH = os.environ.get("BM_PATH", "/Game/HarnessMod")

# The game classifies the parts of a BM class by the name prefix of each component
# (MainBld_, Bld_, clutter_, res_<good>_). Each part is (component name, mesh path, location cm, scale).
DEFAULT_PARTS = [
    ("MainBld_900", "/Engine/BasicShapes/Cube.Cube", (0, 0, 100), (4.0, 4.0, 2.0)),
    ("MainBld_901", "/Engine/BasicShapes/Cone.Cone", (500, 0, 150), (3.0, 3.0, 3.0)),
    ("Bld_902", "/Engine/BasicShapes/Sphere.Sphere", (-500, 0, 150), (3.0, 3.0, 3.0)),
]
# BM_PARTS is a JSON list of the same tuples. Example for one ladder:
# [["clutter_900", "/Game/HarnessMod/Meshes/SM_SiegeLadder.SM_SiegeLadder", [0, 0, 0], [1, 1, 1]]]
PARTS = json.loads(os.environ["BM_PARTS"]) if os.environ.get("BM_PARTS") else DEFAULT_PARTS

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
for index, (part_name, mesh_path, loc, scale) in enumerate(PARTS):
    params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.StaticMeshComponent, blueprint_context=bp)
    handle, fail = sub.add_new_subobject(params)
    unreal.log("BM add %d fail=%s" % (index, fail))
    sub.rename_subobject(handle, part_name)
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    comp.set_editor_property("static_mesh", unreal.load_asset(mesh_path))
    comp.set_editor_property("relative_location", unreal.Vector(*loc))
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(PATH + "/" + NAME)
unreal.log("BM done")
