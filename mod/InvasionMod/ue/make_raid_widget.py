# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_RaidMenu from a stock engine widget (the method of legacy spec 16).
# Why a copy: the WidgetTree root widget is a protected property, so Python cannot set it on a new Widget Blueprint.
# Change update-raid-menu-style (#562): the menu follows the mockup raid-menu-game-style.html (the look of the game's own windows):
# near-black background, centred title "RAIDS" with a thin gold rule, an info line, one flat dark grey panel with rows (diamond marker,
# label, value, separator). No Close in the widget: the menu framework adds the game's Close at the bottom.
# Lua finds the widgets by name (FindAllOf), for i = 0..LINE_COUNT-1:
#   TextBlocks: RaidLabel<i> (the label), RaidLine<i> (the value). Line 3 (the raid levels) is the info line under the title.
#   SizeBoxes:  RaidRow<i> (the whole row; Lua collapses it when its line is empty). Row 3 is the info line.
# The font is a game asset (notes/fonts-textures.md of update-liege-contracts-window-style): an empty stub at the game path is made
# in the editor and never copied into the pak (copy only WBP_RaidMenu.*).
import os
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_RaidMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
FONT_PATH = os.environ.get("RAID_FONT", "Game/UWG/fonts/CombinedFont_Mikadan")  # no leading slash (Git Bash rewrites it)
LINE_COUNT = 5
INFO_INDEX = 3  # the raid levels line
CANVAS_W, CANVAS_H = 1152, 500
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 16, 112, 1120, 372
ROWS_X, ROWS_Y, ROWS_W = 56, 138, 1040
ROW_H = 60
LABEL_X, LABEL_W = 30, 270
VALUE_X, VALUE_W = 310, 720
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.91, 0.78, 0.48, 1)
WHITE = (0.95, 0.93, 0.89, 1)
SOFT = (0.79, 0.76, 0.69, 1)
GREY = (0.56, 0.53, 0.47, 1)
RULE = (0.61, 0.52, 0.33, 1)
LINE = (0.23, 0.215, 0.19, 1)
BACKGROUND = (0.055, 0.055, 0.05, 1)
PANEL = (0.26, 0.25, 0.225, 1)  # flat colour (grungeTiling is too dark)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE

FONT = None


def log(msg):
    unreal.log("RMENU: " + str(msg))


def color(rgba):
    # The values above are the sRGB colours of the mockup; a LinearColor needs linear values.
    r, g, b, a = rgba
    return unreal.LinearColor(r ** 2.2, g ** 2.2, b ** 2.2, a)


def make_stub(asset_path, asset_class, factory):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    folder, name = asset_path.rsplit("/", 1)
    stub = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, asset_class, factory)
    if not stub:
        raise RuntimeError("stub failed: " + asset_path)
    unreal.EditorAssetLibrary.save_asset(asset_path)  # an unsaved stub is a dangling reference in the saved widget
    return stub


def load_game_assets():
    global FONT, FONT_PATH
    FONT_PATH = "/" + FONT_PATH.lstrip("/") if FONT_PATH else ""
    try:
        if FONT_PATH:
            FONT = make_stub(FONT_PATH, unreal.Font, unreal.FontFactory())
    except Exception as error:  # noqa: BLE001 - fallback: the engine font stays
        log("font stub failed (fallback: engine font): %s" % error)
    log("font=%s" % FONT)


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def place(canvas, widget, x, y, w, h):
    slot = canvas.add_child_to_canvas(widget)
    slot.set_position(unreal.Vector2D(x, y))
    slot.set_size(unreal.Vector2D(w, h))
    slot.set_auto_size(False)
    return slot


def style_text(block, size, rgba, spacing, center):
    font = block.get_editor_property("font")
    font.size = size
    if FONT is not None:
        font.set_editor_property("font_object", FONT)
    if spacing:
        font.set_editor_property("letter_spacing", spacing)
    block.set_editor_property("font", font)
    block.set_editor_property("color_and_opacity", unreal.SlateColor(color(rgba)))
    if center:
        block.set_editor_property("justification", unreal.TextJustify.CENTER)
    block.set_visibility(SELF_HIT_TEST_INVISIBLE)


def make_block(tree, name, text, size, rgba, spacing=0, center=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        style_text(block, size, rgba, spacing, center)
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("text style failed for %s: %s" % (name, error))
    return block


def make_flat(tree, canvas, name, rgba, x, y, w, h):
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(rgba))
    border.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, border, x, y, w, h)
    return border


def add_header(tree, canvas):
    title = make_block(tree, "TitleText", "RAIDS", 26, WHITE, spacing=6, center=True)
    place(canvas, title, 0, 18, CANVAS_W, 36)
    make_flat(tree, canvas, "TitleRule", RULE, (CANVAS_W - 290) // 2, 58, 290, 1)


def add_info_row(tree, canvas, i):
    # Label and value side by side, centred as a pair: an Overlay centres a HorizontalBox.
    box = unreal.new_object(unreal.SizeBox, tree, "RaidRow%d" % i)
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", 30)
    overlay = unreal.new_object(unreal.Overlay, tree, "InfoOverlay")
    box.set_content(overlay)
    row = unreal.new_object(unreal.HorizontalBox, tree, "InfoBox")
    slot = overlay.add_child_to_overlay(row)
    slot.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
    label = make_block(tree, "RaidLabel%d" % i, "-", 20, SOFT)
    label_slot = row.add_child_to_horizontal_box(label)
    label_slot.set_padding(unreal.Margin(0, 0, 8, 0))
    row.add_child_to_horizontal_box(make_block(tree, "RaidLine%d" % i, "-", 20, GOLD))
    place(canvas, box, 0, 72, CANVAS_W, 30)


def add_row(tree, column, i):
    box = unreal.new_object(unreal.SizeBox, tree, "RaidRow%d" % i)
    box.set_editor_property("width_override", ROWS_W)
    box.set_editor_property("height_override", ROW_H)
    inner = unreal.new_object(unreal.CanvasPanel, tree, "RowCanvas%d" % i)
    box.set_content(inner)
    make_flat(tree, inner, "RowLine%d" % i, LINE, 0, ROW_H - 4, ROWS_W, 1)
    diamond = make_flat(tree, inner, "RowDiamond%d" % i, GREY, 4, 24, 6, 6)
    try:
        diamond.set_editor_property("render_transform", unreal.WidgetTransform(angle=45))
    except Exception as error:  # noqa: BLE001 - fallback: a square marker
        log("diamond rotation failed: %s" % error)
    place(inner, make_block(tree, "RaidLabel%d" % i, "-", 21, SOFT), LABEL_X, 14, LABEL_W, 30)
    place(inner, make_block(tree, "RaidLine%d" % i, "-", 21, GOLD), VALUE_X, 14, VALUE_W, 30)
    column.add_child(box)


def center_seed(seed):
    # The stock widget puts the seed at 58 percent of the viewport height. Centre the window instead, at its own size.
    slot = seed.get_editor_property("slot")
    slot.set_anchors(unreal.Anchors(unreal.Vector2D(0.5, 0.5), unreal.Vector2D(0.5, 0.5)))
    slot.set_alignment(unreal.Vector2D(0.5, 0.5))
    slot.set_offsets(unreal.Margin(0, 0, CANVAS_W, CANVAS_H))


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    center_seed(seed)
    background = unreal.new_object(unreal.Border, tree, "MenuPanel")
    background.set_editor_property("brush_color", color(BACKGROUND))
    seed.add_child(background)
    box = unreal.new_object(unreal.SizeBox, tree, "MenuBox")
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", CANVAS_H)
    background.set_content(box)
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "RaidCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    panel = unreal.new_object(unreal.Border, tree, "RaidPanel")
    panel.set_editor_property("brush_color", color(PANEL))
    panel.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, panel, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    add_info_row(tree, canvas, INFO_INDEX)
    column = unreal.new_object(unreal.VerticalBox, tree, "RowColumn")
    place(canvas, column, ROWS_X, ROWS_Y, ROWS_W, PANEL_H - (ROWS_Y - PANEL_Y))
    for i in range(LINE_COUNT):
        if i != INFO_INDEX:
            add_row(tree, column, i)


def drop_graphs(bp):
    # The copied graphs refer to widgets that no longer exist.
    lib = unreal.BlueprintEditorLibrary
    graph = lib.find_event_graph(bp)
    log("event graph=%s" % graph)
    if graph:
        lib.remove_graph(bp, graph)
    for name in LEFTOVER_FUNCTIONS:
        found = lib.find_graph(bp, name)
        log("function %s -> %s" % (name, found))
        if found:
            lib.remove_graph(bp, found)
    try:
        lib.remove_unused_variables(bp)
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("remove_unused_variables failed: %s" % error)


def main():
    load_game_assets()
    bp = copy_source()
    tree = unreal.find_object(bp, "WidgetTree")
    seed = unreal.find_object(tree, SEED_WIDGET)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
