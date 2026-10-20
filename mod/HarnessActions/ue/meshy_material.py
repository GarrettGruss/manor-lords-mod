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
# MASTER_MATERIAL=basicshape: parent is the engine material BasicShapeMaterial (in the game paks). It has no
# texture parameter, only the vector parameter `Color`. A colour test: it shows if a plain material draws at all.
BASIC_SHAPE = os.environ.get("MASTER_MATERIAL") == "basicshape"
VECTOR_PARAMS = {}
if BASIC_SHAPE:
    MASTER_PATH = "/Engine/BasicShapes/BasicShapeMaterial"
    TEXTURE_PARAMS, SCALAR_PARAMS, SWITCH_PARAMS = [], {}, {}
    VECTOR_PARAMS = {"Color": unreal.LinearColor(1.0, 0.0, 0.0, 1.0)}
# MASTER_MATERIAL=rgb: parent is M_RGB, the master of the furniture pack instances (MI_Table_02). It has plain colour (BC),
# mask (M) and normal (N) textures, and no palette or paint logic. The instance sets no static switch (notes/import.md).
RGB = os.environ.get("MASTER_MATERIAL") == "rgb"
if RGB:
    MASTER_PATH = "/Game/Assets/Medieval_Furniture_Pack2/Materials/M_RGB"
    TEXTURE_PARAMS = ["BC", "M", "N"]
    SCALAR_PARAMS = {"R Power": 0.6000000238418579, "spec": 0.5}
    SWITCH_PARAMS = {}
# BC_GAME_TEXTURE=<game texture path>: bind the colour map to a texture of the game (a test: does a game texture draw?).
# An empty stub texture is made at that path in the editor project. It is never shipped.
BC_GAME_TEXTURE = os.environ.get("BC_GAME_TEXTURE")
WHITE_TEXTURE = "/Engine/EngineResources/WhiteSquareTexture"
EDIT = unreal.MaterialEditingLibrary
# TEXTURE_NEVER_STREAM=1: cook every mesh texture without streaming (all mips in the package). A texture test.
NEVER_STREAM = os.environ.get("TEXTURE_NEVER_STREAM") == "1"


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
        if NEVER_STREAM:
            texture.set_editor_property("never_stream", True)
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
    if BASIC_SHAPE:
        unreal.log("MATERIAL basicshape vector params %s" % [str(n) for n in EDIT.get_vector_parameter_names(master)])
        for name, value in VECTOR_PARAMS.items():
            EDIT.set_material_instance_vector_parameter_value(instance, name, value)
        EDIT.update_material_instance(instance)
        unreal.EditorAssetLibrary.save_asset(instance_path)
        for index in range(len(mesh.static_materials)):
            mesh.set_material(index, instance)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        return instance
    white = unreal.load_asset(WHITE_TEXTURE)
    color_name, normal_name = ("Base", "Normal") if MEGASCANS else (("BC", "N") if RGB else ("d", "n"))
    color_texture = load_texture(folder, "texture_0")
    if BC_GAME_TEXTURE:
        if not unreal.EditorAssetLibrary.does_asset_exist(BC_GAME_TEXTURE):
            unreal.EditorAssetLibrary.duplicate_asset(WHITE_TEXTURE, BC_GAME_TEXTURE)
        color_texture = unreal.load_asset(BC_GAME_TEXTURE)
    EDIT.set_material_instance_texture_parameter_value(instance, color_name, color_texture)
    EDIT.set_material_instance_texture_parameter_value(instance, normal_name, load_texture(folder, "texture_0_normal"))
    if RGB:
        EDIT.set_material_instance_texture_parameter_value(instance, "M", load_texture(folder, spec_name))
    else:
        EDIT.set_material_instance_texture_parameter_value(instance, "AO", white)
    if not MEGASCANS and not RGB:
        EDIT.set_material_instance_texture_parameter_value(instance, "spec", load_texture(folder, spec_name))
    for name, value in SCALAR_PARAMS.items():
        EDIT.set_material_instance_scalar_parameter_value(instance, name, value)
    for name, value in SWITCH_PARAMS.items():
        EDIT.set_material_instance_static_switch_parameter_value(instance, name, value)
    if RGB:  # the game instances of M_RGB set this base property
        overrides = instance.get_editor_property("base_property_overrides")
        overrides.set_editor_property("override_dithered_lod_transition", True)
        overrides.set_editor_property("dithered_lod_transition", True)
        instance.set_editor_property("base_property_overrides", overrides)
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
