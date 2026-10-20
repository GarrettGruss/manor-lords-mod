"""Spec 33. Give a Meshy mesh a material that the game can draw.

Why: a material that is cooked here has no shader code in the pak. The shader code lives in the game's own
shader library (`ShaderArchive-ManorLords_Chunk0-*`). The game then draws a fallback grey. A material
INSTANCE of a game master material needs no new shader code, because the game already has it.

How: make a stub of the game master `tudorWall01` (same path, same parameter names) so that the editor accepts
an instance. Make an instance with our textures. The stub is never shipped: copy only the files under
/Game/HarnessMod to the pak. At run time the game loads its real master.
Parameters were read from the game's own instance `tudorWall01_combined` (see the spec 33 notes).
"""
import os
import unreal

MASTER_PATH = "/Game/NotStronghold/Buildings/TudorWall/tudorWall01"
TEXTURE_PARAMS = ["AO", "d", "n", "spec"]
SCALAR_PARAMS = {"aoFromGroundFade": 512.0, "br": 0.5, "dirt tiling": 2.0, "n str": 0.0, "R": 1.0, "spec": 0.2}
SWITCH_PARAMS = {"Dirt?": False, "spec map?": True}
# MASTER_MATERIAL=megascans: parent is the master of the game's own MI_SS_Shrine5, because tudorWall01 renders
# brown wood and thatch pale. Names and values were read from MI_SS_Shrine5 (notes/swap-shrines.md).
MEGASCANS = os.environ.get("MASTER_MATERIAL") == "megascans"
if MEGASCANS:
    MASTER_PATH = "/Game/Megascans/MegascansStandard"
    TEXTURE_PARAMS = ["Base", "Normal", "AO"]
    SCALAR_PARAMS = {"AO": 0.7, "Roughness": 0.7942860126495361, "spec": 0.400952011346817, "diff mul": 1.0, "blendSnow": 0.0, "proxyFx_snow": 0.0}
    SWITCH_PARAMS = {"Has Normal": True, "Has roughness?": False, "Use AO": True,
                    "applyWetnessAndSnowFx": False, "useVertexForSnow": False}
WHITE_TEXTURE = "/Engine/EngineResources/WhiteSquareTexture"
EDIT = unreal.MaterialEditingLibrary


def ensure_stub_master():
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        return unreal.load_asset(MASTER_PATH)
    folder, name = MASTER_PATH.rsplit("/", 1)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    for index, param in enumerate(TEXTURE_PARAMS):
        node = EDIT.create_material_expression(master, unreal.MaterialExpressionTextureSampleParameter2D, -600, index * 200)
        node.set_editor_property("parameter_name", param)
    for index, param in enumerate(SCALAR_PARAMS):
        node = EDIT.create_material_expression(master, unreal.MaterialExpressionScalarParameter, -1000, index * 100)
        node.set_editor_property("parameter_name", param)
    for index, param in enumerate(SWITCH_PARAMS):
        node = EDIT.create_material_expression(master, unreal.MaterialExpressionStaticSwitchParameter, -1400, index * 200)
        node.set_editor_property("parameter_name", param)
    EDIT.recompile_material(master)
    unreal.EditorAssetLibrary.save_asset(MASTER_PATH)
    unreal.log("MATERIAL stub master made at " + MASTER_PATH)
    return master


def load_texture(folder: str, name: str):
    texture = unreal.load_asset(folder + "/" + name)
    if texture is None:
        raise RuntimeError("texture missing: " + folder + "/" + name)
    return texture


def fix_texture_settings(folder: str) -> None:
    """Colour map is sRGB. The normal map is a normal map. The rest is linear data."""
    for name in ("texture_0", "texture_0_normal", "texture_0_roughness", "texture_0_metallic", "texture_0_emission"):
        path = folder + "/" + name
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        texture = unreal.load_asset(path)
        if name == "texture_0_normal":
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("srgb", False)
        elif name == "texture_0":
            texture.set_editor_property("srgb", True)
        else:
            texture.set_editor_property("srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(texture)
        unreal.log("MATERIAL texture %s srgb=%s comp=%s" % (name, texture.get_editor_property("srgb"), texture.get_editor_property("compression_settings")))


def make_game_material(mesh, folder: str, spec_name: str = "texture_0_roughness"):
    """Replace the imported material of `mesh` with an instance of the game master. Return the instance."""
    master = ensure_stub_master()
    fix_texture_settings(folder)
    instance_path = folder + "/MI_Meshy"
    if unreal.EditorAssetLibrary.does_asset_exist(instance_path):
        unreal.EditorAssetLibrary.delete_asset(instance_path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    instance = tools.create_asset("MI_Meshy", folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", master)
    white = unreal.load_asset(WHITE_TEXTURE)
    color_name, normal_name = ("Base", "Normal") if MEGASCANS else ("d", "n")
    EDIT.set_material_instance_texture_parameter_value(instance, color_name, load_texture(folder, "texture_0"))
    EDIT.set_material_instance_texture_parameter_value(instance, normal_name, load_texture(folder, "texture_0_normal"))
    EDIT.set_material_instance_texture_parameter_value(instance, "AO", white)
    if not MEGASCANS:
        EDIT.set_material_instance_texture_parameter_value(instance, "spec", load_texture(folder, spec_name))
    for name, value in SCALAR_PARAMS.items():
        EDIT.set_material_instance_scalar_parameter_value(instance, name, value)
    for name, value in SWITCH_PARAMS.items():
        EDIT.set_material_instance_static_switch_parameter_value(instance, name, value)
    EDIT.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_asset(instance_path)
    slots = mesh.static_materials
    for index in range(len(slots)):
        mesh.set_material(index, instance)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    old = folder + "/Material_001"
    if unreal.EditorAssetLibrary.does_asset_exist(old):
        unreal.EditorAssetLibrary.delete_asset(old)
    unreal.log("MATERIAL instance %s parent %s slots %d" % (instance_path, MASTER_PATH, len(slots)))
    return instance
