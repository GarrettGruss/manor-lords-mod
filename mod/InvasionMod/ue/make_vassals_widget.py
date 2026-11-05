# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_Vassals from a stock engine widget (same method as make_liege_widget.py and make_scenario_settings_widget.py).
# Change add-vassals-menu (#564): the Vassals window follows the mockup vassals-menu.html (the look of the game's own windows):
# near-black background, centred title in spaced capitals with a thin gold rule, one header line with three gold values, one dark grey
# panel with three vassal cards, serif text, plain-text policy options (the selected one is gold and underlined by Lua) and a plain-text
# "Restore the village". No Close in the widget (the menu framework draws the game's Close at the bottom middle).
# The vassals are data, but a pak asset is fixed, so the asset holds a POOL of 3 cards on ONE canvas. Lua fills the texts and tints the
# marks. Lua puts an invisible WBP_ClickButton (HarnessClickHooks) into each button Border on top of the texts.
# Game assets (notes of the archived changes update-liege-contracts-window-style and update-scenario-settings-window-style): the font is
# referenced by its game path. The editor has no game content, so an empty stub asset is made at the same path; the stub is never copied
# into the pak (copy only WBP_Vassals.*).
# Names (card c = 0..2; stat row r = 0..5: Status, Rich resources, Tribute / month, Families, Buildings, Vassal for; policy p = 0..2):
#   TextBlocks: TitleText, HeadLabel<i>, HeadValue<i> (i = 0..2), CardRegion<c>, CardLord<c>, StatLabel<c>_<r>, StatValue<c>_<r>, NoteText<c>,
#               PolicyLabel<c>, PolicyText<c>_<p>, PolicyHint<c>, RestoreText<c>, RestoreHint<c>
#   Borders:    Card<c> (tint and dim target), Diamond<c>_<r>, Line<c>_<r>, Under<c>_<p> (tinted by Lua),
#               PolicyButton<c>_<p>, RestoreButton<c> (button borders)
import os
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_Vassals"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
FONT_PATH = os.environ.get("VASSALS_FONT", "Game/UWG/fonts/CombinedFont_Mikadan")  # no leading slash (Git Bash rewrites it)
TYPEFACE = os.environ.get("VASSALS_TYPEFACE", "")
CARDS, STAT_ROWS, POLICIES = 3, 6, 3
CANVAS_W, CANVAS_H = 1152, 654
PANEL_X, PANEL_Y, PANEL_W, PANEL_H = 16, 108, 1120, 512
PANEL_PAD, CARD_GAP = 14, 12
CARD_W = (PANEL_W - 2 * PANEL_PAD - (CARDS - 1) * CARD_GAP) // CARDS
CARD_H = PANEL_H - 2 * PANEL_PAD
PAD = 16                                  # inside a card
HEAD_H = 64
ROW_TOP = 78
ROW_HEIGHTS = [40, 40, 52, 40, 40, 40]    # the tribute row has room for two lines
LABEL_W = 132
VALUE_X = PAD + LABEL_W + 10
VALUE_W = CARD_W - PAD - VALUE_X
NOTE_Y, NOTE_H = 338, 52
POLICY_LABEL_Y, POLICY_Y, UNDER_Y, HINT_Y = 396, 414, 446, 456
RESTORE_Y, RESTORE_HINT_Y = 404, 442
OPTION_W = 106
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.91, 0.78, 0.48, 1)
WHITE = (0.95, 0.93, 0.89, 1)
SOFT = (0.79, 0.76, 0.69, 1)
MUTED = (0.66, 0.63, 0.56, 1)
GREY = (0.56, 0.53, 0.47, 1)
RULE = (0.61, 0.52, 0.33, 1)
LINE = (0.23, 0.215, 0.19, 1)
BACKGROUND = (0.055, 0.055, 0.05, 1)
PANEL = (0.26, 0.25, 0.225, 1)  # flat colour (grungeTiling is too dark)
HEAD_BG = (0.06, 0.06, 0.05, 0.5)
CARD_BG = (0.08, 0.075, 0.065, 0.55)
CARD_TOP = (0.29, 0.275, 0.24, 1)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE

FONT = None


def log(msg):
    unreal.log("VASSALS: " + str(msg))


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


def style_text(block, size, rgba, spacing, justify, wrap):
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
    if justify == "center":
        block.set_editor_property("justification", unreal.TextJustify.CENTER)
    elif justify == "right":
        block.set_editor_property("justification", unreal.TextJustify.RIGHT)
    if wrap:
        block.set_editor_property("auto_wrap_text", True)
    block.set_visibility(SELF_HIT_TEST_INVISIBLE)


def new_text(tree, name, text, size=16, rgba=WHITE, spacing=0, justify="left", wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        style_text(block, size, rgba, spacing, justify, wrap)
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("text style failed for %s: %s" % (name, error))
    return block


def make_text(tree, canvas, name, text, x, y, w, h, **style):
    block = new_text(tree, name, text, **style)
    place(canvas, block, x, y, w, h)
    return block


def make_flat(tree, canvas, name, rgba, x, y, w, h):
    # A flat colour block that does not take clicks.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(rgba))
    border.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, border, x, y, w, h)
    return border


def make_diamond(tree, canvas, name, x, y):
    border = make_flat(tree, canvas, name, CLEAR, x, y, 6, 6)  # Lua tints it grey when the row shows
    try:
        border.set_editor_property("render_transform", unreal.WidgetTransform(angle=45))
    except Exception as error:  # noqa: BLE001 - fallback: a square marker
        log("diamond rotation failed: %s" % error)
    return border


def make_button(tree, canvas, name, x, y, w, h):
    # Lua puts a WBP_ClickButton into this border: its OnClicked event is hookable, a Button here is not.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(CLEAR))  # a Border paints white by default
    place(canvas, border, x, y, w, h)
    return border


def add_header(tree, canvas):
    make_text(tree, canvas, "TitleText", "VASSALS", 0, 18, CANVAS_W, 36, size=26, rgba=WHITE, spacing=6, justify="center")
    make_flat(tree, canvas, "TitleRule", RULE, (CANVAS_W - 290) // 2, 58, 290, 1)
    # One centred row: the three label and value pairs side by side, so a long tribute list pushes the others apart.
    bar = unreal.new_object(unreal.Border, tree, "HeadBar")
    bar.set_editor_property("brush_color", color(CLEAR))
    bar.set_visibility(HIT_TEST_INVISIBLE)
    bar.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
    row = unreal.new_object(unreal.HorizontalBox, tree, "HeadRow")
    for i in range(3):
        slot = row.add_child(new_text(tree, "HeadLabel%d" % i, "-", size=15, rgba=SOFT))
        slot.set_padding(unreal.Margin(0, 0, 7, 0))
        slot = row.add_child(new_text(tree, "HeadValue%d" % i, "-", size=15, rgba=GOLD))
        slot.set_padding(unreal.Margin(0, 0, 0 if i == 2 else 48, 0))
    bar.set_content(row)
    place(canvas, bar, 0, 68, CANVAS_W, 28)


def add_panel(tree, canvas):
    panel = unreal.new_object(unreal.Border, tree, "VassalPanel")
    panel.set_editor_property("brush_color", color(PANEL))
    panel.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, panel, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)


def add_stat_rows(tree, box, c):
    y = ROW_TOP
    for r in range(STAT_ROWS):
        key = "%d_%d" % (c, r)
        height = ROW_HEIGHTS[r]
        make_diamond(tree, box, "Diamond" + key, PAD, y + 15)
        make_text(tree, box, "StatLabel" + key, "-", PAD + 20, y + 8, LABEL_W - 20, 26, size=15, rgba=WHITE)
        make_text(tree, box, "StatValue" + key, "-", VALUE_X, y + 9, VALUE_W, height - 8, size=14, rgba=GOLD, justify="right", wrap=True)
        make_flat(tree, box, "Line" + key, CLEAR, PAD, y + height - 2, CARD_W - 2 * PAD, 1)
        y += height


def add_policy_row(tree, box, c):
    inner = CARD_W - 2 * PAD
    make_text(tree, box, "PolicyLabel%d" % c, "-", 0, POLICY_LABEL_Y, CARD_W, 18, size=12, rgba=MUTED, spacing=2, justify="center")
    first = (CARD_W - POLICIES * OPTION_W) // 2
    for p in range(POLICIES):
        key = "%d_%d" % (c, p)
        x = first + p * OPTION_W
        make_text(tree, box, "PolicyText" + key, "-", x, POLICY_Y, OPTION_W, 30, size=19, rgba=GREY, justify="center")
        make_flat(tree, box, "Under" + key, CLEAR, x + 20, UNDER_Y, OPTION_W - 40, 1)
    make_text(tree, box, "PolicyHint%d" % c, "-", PAD, HINT_Y, inner, 20, size=13, rgba=MUTED, justify="center")


def add_restore(tree, box, c):
    inner = CARD_W - 2 * PAD
    make_text(tree, box, "RestoreText%d" % c, "-", 0, RESTORE_Y, CARD_W, 32, size=22, rgba=WHITE, justify="center")
    make_text(tree, box, "RestoreHint%d" % c, "-", PAD, RESTORE_HINT_Y, inner, 20, size=13, rgba=SOFT, justify="center")


def add_card(tree, canvas, c, x, y):
    card = unreal.new_object(unreal.Border, tree, "Card%d" % c)  # tint and dim target: Lua sets its brush colour and render opacity
    card.set_editor_property("brush_color", color(CARD_BG))
    card.set_visibility(SELF_HIT_TEST_INVISIBLE)
    box = unreal.new_object(unreal.CanvasPanel, tree, "CardCanvas%d" % c)
    card.set_content(box)
    place(canvas, card, x, y, CARD_W, CARD_H)
    make_flat(tree, box, "CardTop%d" % c, CARD_TOP, 0, 0, CARD_W, 1)
    make_flat(tree, box, "CardHead%d" % c, HEAD_BG, 0, 0, CARD_W, HEAD_H)
    make_text(tree, box, "CardRegion%d" % c, "-", 0, 4, CARD_W, 32, size=22, rgba=WHITE, justify="center")
    make_text(tree, box, "CardLord%d" % c, "", 0, 40, CARD_W, 20, size=14, rgba=MUTED, justify="center")
    add_stat_rows(tree, box, c)
    make_text(tree, box, "NoteText%d" % c, "", PAD, NOTE_Y, CARD_W - 2 * PAD, NOTE_H, size=13, rgba=MUTED, wrap=True)
    add_policy_row(tree, box, c)
    add_restore(tree, box, c)
    # The buttons come last in the card so they lie on top and take the clicks.
    first = (CARD_W - POLICIES * OPTION_W) // 2
    for p in range(POLICIES):
        make_button(tree, box, "PolicyButton%d_%d" % (c, p), first + p * OPTION_W, POLICY_Y - 4, OPTION_W, 42)
    make_button(tree, box, "RestoreButton%d" % c, 38, RESTORE_Y - 6, CARD_W - 76, 52)


def add_cards(tree, canvas):
    for c in range(CARDS):
        add_card(tree, canvas, c, PANEL_X + PANEL_PAD + c * (CARD_W + CARD_GAP), PANEL_Y + PANEL_PAD)


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
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "VassalsCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    add_panel(tree, canvas)
    add_cards(tree, canvas)


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
