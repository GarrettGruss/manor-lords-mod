import os
import unreal

# Large stable (issue 104): two ox shed parts side by side and a `gathering` Scene.
# The game mesh is not in the UE project. A stand-in asset (a copy of the engine Cube) is made at the
# game path, so the cooked Blueprint points at the real game mesh. Do not pack the stand-in.
NAME = os.environ.get("BM_NAME", "BM_HarnessLargeStable")
PATH = "/Game/HarnessMod"
SHED_MESH = "/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_OxShed_UBeam"
SHED_Y = float(os.environ.get("SHED_Y", "650"))
PROBES = os.environ.get("BM_PROBES", "0") == "1"

MESH_PARTS = [
    ("MainBld_900", (-5.0, 15.3, 0.0), 0.9),
    ("MainBld_901", (-5.0, 15.3 + SHED_Y, 0.0), 0.9),
]
SCENE_PARTS = [("gathering", (304.6, 15.3 + SHED_Y / 2.0, 0.0))]
if PROBES:
    SCENE_PARTS += [("Scene_%d" % i, loc) for i, loc in enumerate(
        [(74.7, 208.3, 0.0), (75.1, -142.9, 0.0), (74.7, 858.3, 0.0), (75.1, 507.1, 0.0)])]

if not unreal.EditorAssetLibrary.does_asset_exist(SHED_MESH):
    unreal.EditorAssetLibrary.duplicate_asset("/Engine/BasicShapes/Cube", SHED_MESH)
    unreal.EditorAssetLibrary.save_asset(SHED_MESH)

tools = unreal.AssetToolsHelpers.get_asset_tools()
if unreal.EditorAssetLibrary.does_asset_exist(PATH + "/" + NAME):
    unreal.EditorAssetLibrary.delete_asset(PATH + "/" + NAME)
factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.StaticMeshActor)
bp = tools.create_asset(NAME, PATH, unreal.Blueprint, factory)
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
root = sub.k2_gather_subobject_data_for_blueprint(bp)[0]


def add_component(component_class, name, location, yaw):
    params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=component_class, blueprint_context=bp)
    handle, fail = sub.add_new_subobject(params)
    unreal.log("BM add %s fail=%s" % (name, fail))
    sub.rename_subobject(handle, name)
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    comp.set_editor_property("relative_location", unreal.Vector(*location))
    comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, yaw, 0.0))
    return comp


for part_name, location, yaw in MESH_PARTS:
    comp = add_component(unreal.StaticMeshComponent, part_name, location, yaw)
    comp.set_editor_property("static_mesh", unreal.load_asset(SHED_MESH))
for part_name, location in SCENE_PARTS:
    add_component(unreal.SceneComponent, part_name, location, 0.0)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(PATH + "/" + NAME)
unreal.log("BM done")
