# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_ScenarioSettings from a stock engine widget (same method as make_liege_widget.py).
# Change update-scenario-settings-window-style (#540): the start screen follows the mockup scenario-settings-game-style.html (the look of
# the game's own windows): near-black background, centred title in spaced capitals with a thin gold rule, one dark grey panel in two
# columns (the scenario text on the left, five setting rows on the right), serif text, plain-text options (the selected one is gold and
# underlined by Lua), "Use defaults" and a large "Begin the game". No Close in the widget and none from the menu framework.
# The texts of the options and the two buttons are text blocks of this widget (the game font). Lua puts an invisible WBP_ClickButton
# (HarnessClickHooks) into each button Border on top of them. Lua finds widgets by name:
#   TextBlocks: SettingsTitle, BackgroundText, RowLabel<r>, OptText<r>_<c>, DefaultsText, BeginText   (r = 0..4, c = 0..3)
#   Borders:    Choice<r>_<c>, DefaultsButton, BeginButton (button Borders), Under<r>_<c> (the underline of the selected option)
# Game assets (notes/fonts-textures.md): the font is referenced by its game path. The editor has no game content, so an empty stub
# asset is made at the same path; the stub is never copied into the pak (copy only WBP_ScenarioSettings.*).
import os
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_ScenarioSettings"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
FONT_PATH = os.environ.get("SETTINGS_FONT", "Game/UWG/fonts/CombinedFont_Mikadan")  # no leading slash (Git Bash rewrites it)
TYPEFACE = os.environ.get("SETTINGS_TYPEFACE", "")
ROW_COUNT = 5
CHOICE_COUNT = 4
CHOICES_OF_ROW = [4, 4, 4, 3, 3]
CANVAS_W, CANVAS_H = 1152, 654
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 16, 76, 1120, 492
LEFT_X, LEFT_W = 54, 352
RIGHT_X, RIGHT_W = 444, 654
HEAD_Y, HEAD_H = 110, 34
BODY_Y = 160
ROW_H = 64
LABEL_X, LABEL_W = RIGHT_X + 20, 180
OPTION_X = RIGHT_X + 206
OPTION_AREA = RIGHT_X + RIGHT_W - OPTION_X
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.91, 0.78, 0.48, 1)
WHITE = (0.95, 0.93, 0.89, 1)
SOFT = (0.79, 0.76, 0.69, 1)
GREY = (0.56, 0.53, 0.47, 1)
RULE = (0.61, 0.52, 0.33, 1)
LINE = (0.23, 0.215, 0.19, 1)
BACKGROUND = (0.055, 0.055, 0.05, 1)
PANEL = (0.26, 0.25, 0.225, 1)  # flat colour (grungeTiling is too dark, notes/fonts-textures.md)
HEAD_BG = (0.06, 0.06, 0.05, 0.5)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE

FONT = None


def log(msg):
    unreal.log("SSMENU: " + str(msg))


def color(rgba):
    # The values above are the sRGB colours of the mockup; a LinearColor needs linear values.
    r, g, b, a = rgba
    return unreal.LinearColor(r ** 2.2, g ** 2.2, b ** 2.2, a)


def make_stub(asset_path, asset_class, factory):
    # An empty stand-in at the game's path. The cooked widget refers to the path; the game loads the real asset from its own pak.
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


def style_text(block, size, rgba, spacing, center, wrap):
    font = block.get_editor_property("font")
    font.size = size
    if FONT is not None:
        font.set_editor_property("font_object", FONT)
        if TYPEFACE:
            font.set_editor_property("typeface_font_name", TYPEFACE)
    if spacing:
        font.set_editor_property("letter_spacing", spacing)
    block.set_editor_property("font", font)
    block.set_editor_property("color_and_opacity", unreal.SlateColor(color(rgba)))
    if center:
        block.set_editor_property("justification", unreal.TextJustify.CENTER)
    if wrap:
        block.set_editor_property("auto_wrap_text", True)
    block.set_visibility(SELF_HIT_TEST_INVISIBLE)


def make_text(tree, canvas, name, text, x, y, w, h, size=16, rgba=WHITE, spacing=0, center=False, wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        style_text(block, size, rgba, spacing, center, wrap)
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("text style failed for %s: %s" % (name, error))
    place(canvas, block, x, y, w, h)
    return block


def make_flat(tree, canvas, name, rgba, x, y, w, h):
    # A flat colour block that does not take clicks.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(rgba))
    border.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, border, x, y, w, h)
    return border


def make_button(tree, canvas, name, x, y, w, h):
    # Lua puts a WBP_ClickButton into this border (spec 34): its OnClicked event is hookable, a Button here is not.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(CLEAR))  # a Border paints white by default
    place(canvas, border, x, y, w, h)
    return border


def make_diamond(tree, canvas, name, x, y):
    border = make_flat(tree, canvas, name, GREY, x, y, 6, 6)
    try:
        border.set_editor_property("render_transform", unreal.WidgetTransform(angle=45))
    except Exception as error:  # noqa: BLE001 - fallback: a square marker
        log("diamond rotation failed: %s" % error)


def add_header(tree, canvas):
    make_text(tree, canvas, "SettingsTitle", "THE HUSSITES ARE COMING", 0, 18, CANVAS_W, 36, size=26, rgba=WHITE, spacing=6, center=True)
    make_flat(tree, canvas, "TitleRule", RULE, (CANVAS_W - 290) // 2, 58, 290, 1)


def add_columns(tree, canvas):
    panel = unreal.new_object(unreal.Border, tree, "SettingsPanel")
    panel.set_editor_property("brush_color", color(PANEL))
    panel.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, panel, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
    make_flat(tree, canvas, "LeftHeadBar", HEAD_BG, LEFT_X, HEAD_Y, LEFT_W, HEAD_H)
    make_text(tree, canvas, "LeftHeading", "The Scenario", LEFT_X, HEAD_Y + 4, LEFT_W, 28, size=19, rgba=WHITE, center=True)
    make_flat(tree, canvas, "RightHeadBar", HEAD_BG, RIGHT_X, HEAD_Y, RIGHT_W, HEAD_H)
    make_text(tree, canvas, "RightHeading", "Settings", RIGHT_X, HEAD_Y + 4, RIGHT_W, 28, size=19, rgba=WHITE, center=True)
    make_text(tree, canvas, "BackgroundText", "-", LEFT_X, BODY_Y, LEFT_W, PANEL_H - (BODY_Y - PANEL_Y) - 20, size=16, rgba=WHITE, wrap=True)


def add_row(tree, canvas, row):
    y = BODY_Y + row * ROW_H
    count = CHOICES_OF_ROW[row]
    slot_w = OPTION_AREA // count
    make_flat(tree, canvas, "RowLine%d" % row, LINE, RIGHT_X, y + ROW_H - 4, RIGHT_W, 1)
    make_diamond(tree, canvas, "RowDiamond%d" % row, RIGHT_X + 4, y + 22)
    make_text(tree, canvas, "RowLabel%d" % row, "-", LABEL_X, y + 12, LABEL_W, 28, size=18, rgba=WHITE)
    for choice in range(CHOICE_COUNT):
        x = OPTION_X + choice * slot_w
        make_text(tree, canvas, "OptText%d_%d" % (row, choice), "-", x, y + 14, slot_w, 26, size=16, rgba=GREY, center=True)
        make_flat(tree, canvas, "Under%d_%d" % (row, choice), GOLD, x + 18, y + 40, slot_w - 36, 1).set_visibility(unreal.SlateVisibility.COLLAPSED)
    return y, slot_w


def add_buttons(tree, canvas):
    make_text(tree, canvas, "DefaultsText", "-", 280, 592, 240, 32, size=20, rgba=SOFT, center=True)
    make_text(tree, canvas, "BeginText", "-", 640, 586, 300, 44, size=30, rgba=WHITE, center=True)
    for name, x in (("FlourishLeft", 600), ("FlourishRight", 944)):
        make_text(tree, canvas, name, "❧", x, 596, 30, 34, size=22, rgba=SOFT, center=True)
    make_button(tree, canvas, "DefaultsButton", 280, 586, 240, 44)
    make_button(tree, canvas, "BeginButton", 600, 580, 374, 56)


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
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "SettingsCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    add_columns(tree, canvas)
    rows = [add_row(tree, canvas, row) for row in range(ROW_COUNT)]
    add_buttons(tree, canvas)
    # The choice buttons come last so they lie on top and take the clicks.
    for row, (y, slot_w) in enumerate(rows):
        for choice in range(CHOICES_OF_ROW[row]):
            make_button(tree, canvas, "Choice%d_%d" % (row, choice), OPTION_X + choice * slot_w, y + 6, slot_w, 44)


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
