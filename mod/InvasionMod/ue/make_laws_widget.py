# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_Laws from a stock engine widget (same method as make_liege_widget.py).
# Change add-laws-menu (#563): the Laws menu follows the approved mockup mockups/laws-menu.html (Laws.dc.html of the owner, 2026-11-04):
# near-black background, centred title with a thin gold rule, one header line (laws in force, enact and revoke actions of the year,
# unlocked count), the refresh line, a filter row (All, Unlocked, Locked), one dark grey panel with nine law cards (3 x 3), and a confirm
# dialog on top. No Close in the widget: the menu framework draws the game's Close at the bottom middle.
# The laws are data (data/tech_tree/tree.json), but a pak asset is fixed, so the asset holds a POOL of 9 cards on ONE canvas. Lua fills them
# (core/menu.lua, features/laws_menu/init.lua). Lua finds widgets by name and puts a WBP_ClickButton into each button Border
# (HarnessClickHooks). The texts of the buttons are text blocks of this widget; the click buttons on top of them are invisible.
# Hiding is done by empty text and clear brush colours, not by visibility (notes of change update-scenario-settings-window-style).
# Game assets (notes of change update-liege-contracts-window-style, fonts-textures.md): the font is referenced by its game path. The editor
# has no game content, so an empty stub asset is made at the same path; the stub is never copied into the pak (copy only WBP_Laws.*).
# Names (card k = 0..8, effect line j = 0..2, filter f = 0..2):
#   TextBlocks: TitleText, HdrSlotsValue, HdrSlotsMax, HdrEnactValue, HdrRevokeValue, HdrUnlockValue, RefreshText, NoticeText,
#               FilterText<f>, NameText<k>, StatusText<k>, SourceText<k>, EffText<k>_<j>, HintText<k>, ActText<k>,
#               DlgTitle, DlgQuestion, DlgEff<j>, DlgCost, DlgCancelText, DlgConfirmText
#   Borders:    Card<k> (card fill and dim target), CardTop<k>, ActUnder<k>, FilterUnder<f>, DlgShade, DlgPanel, DlgRule, DlgConfirmUnder,
#               button Borders: ActButton<k>, FilterButton<f>, DlgCancelButton, DlgConfirmButton
import os
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_Laws"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
FONT_PATH = os.environ.get("LAWS_FONT", "Game/UWG/fonts/CombinedFont_Mikadan")  # no leading slash (Git Bash rewrites it)
TYPEFACE = os.environ.get("LAWS_TYPEFACE", "")
CARDS, COLUMNS, EFFECT_LINES, FILTERS = 9, 3, 3, 3
CANVAS_W, CANVAS_H = 1152, 672
PANEL_X, PANEL_Y, PANEL_W = 16, 148, 1120
PANEL_PAD, CARD_H, CARD_GAP = 14, 150, 12
CARD_W = (PANEL_W - 2 * PANEL_PAD - (COLUMNS - 1) * CARD_GAP) // COLUMNS
PANEL_H = 2 * PANEL_PAD + 3 * CARD_H + 2 * CARD_GAP
PAD = 14                       # inside a card
FILTER_W, FILTER_GAP = 110, 18
DIALOG_W, DIALOG_H = 560, 330
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.91, 0.78, 0.48, 1)
WHITE = (0.95, 0.93, 0.89, 1)
SOFT = (0.79, 0.76, 0.69, 1)
MUTED = (0.56, 0.53, 0.47, 1)
RULE = (0.61, 0.52, 0.33, 1)
BACKGROUND = (0.055, 0.055, 0.05, 1)
PANEL = (0.26, 0.25, 0.225, 1)  # flat colour (grungeTiling is too dark)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE

FONT = None


def log(msg):
    unreal.log("LAWS: " + str(msg))


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


def style_text(block, size, rgba, spacing, align, wrap):
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
    if align == "center":
        block.set_editor_property("justification", unreal.TextJustify.CENTER)
    elif align == "right":
        block.set_editor_property("justification", unreal.TextJustify.RIGHT)
    if wrap:
        block.set_editor_property("auto_wrap_text", True)
    block.set_visibility(SELF_HIT_TEST_INVISIBLE)


def new_text(tree, name, text, size=16, rgba=WHITE, spacing=0, align="left", wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        style_text(block, size, rgba, spacing, align, wrap)
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("text style failed for %s: %s" % (name, error))
    return block


def make_text(tree, canvas, name, text, x, y, w, h, **style):
    block = new_text(tree, name, text, **style)
    place(canvas, block, x, y, w, h)
    return block


def make_flat(tree, canvas, name, rgba, x, y, w, h):
    # A flat colour block that does not take clicks. Lua changes the brush colour of the named ones.
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


def add_header(tree, canvas):
    make_text(tree, canvas, "TitleText", "LAWS", 0, 14, CANVAS_W, 32, size=24, rgba=WHITE, spacing=5, align="center")
    make_flat(tree, canvas, "TitleRule", RULE, (CANVAS_W - 240) // 2, 50, 240, 1)
    bar = unreal.new_object(unreal.Border, tree, "HeaderBar")
    bar.set_editor_property("brush_color", color(CLEAR))
    bar.set_visibility(HIT_TEST_INVISIBLE)
    bar.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
    row = unreal.new_object(unreal.HorizontalBox, tree, "HeaderRow")
    # (name, text, colour, size, space after). Lua writes the value texts and their colour.
    parts = [("HdrSlotsLabel", "Laws in force:", SOFT, 6), ("HdrSlotsValue", "0 / 1", GOLD, 6), ("HdrSlotsMax", "(max 5)", MUTED, 40),
             ("HdrEnactLabel", "Enact this year:", SOFT, 6), ("HdrEnactValue", "1 / 1", GOLD, 40),
             ("HdrRevokeLabel", "Revoke this year:", SOFT, 6), ("HdrRevokeValue", "1 / 1", GOLD, 40),
             ("HdrUnlockLabel", "Unlocked:", SOFT, 6), ("HdrUnlockValue", "0 of 9", GOLD, 0)]
    for name, text, rgba, gap in parts:
        slot = row.add_child(new_text(tree, name, text, size=15, rgba=rgba))
        slot.set_padding(unreal.Margin(0, 0, gap, 0))
    bar.set_content(row)
    place(canvas, bar, 0, 60, CANVAS_W, 28)
    make_text(tree, canvas, "RefreshText", "", 0, 90, CANVAS_W, 20, size=13, rgba=MUTED, align="center")


def add_filters(tree, canvas):
    start = (CANVAS_W - (FILTERS * FILTER_W + (FILTERS - 1) * FILTER_GAP)) // 2
    for f in range(FILTERS):
        x = start + f * (FILTER_W + FILTER_GAP)
        make_text(tree, canvas, "FilterText%d" % f, "-", x, 114, FILTER_W, 24, size=18, rgba=MUTED, align="center")
        make_flat(tree, canvas, "FilterUnder%d" % f, CLEAR, x + 20, 140, FILTER_W - 40, 1)
        make_button(tree, canvas, "FilterButton%d" % f, x, 110, FILTER_W, 32)


def add_panel(tree, canvas):
    panel = unreal.new_object(unreal.Border, tree, "LawsPanel")
    panel.set_editor_property("brush_color", color(PANEL))
    panel.set_visibility(HIT_TEST_INVISIBLE)
    place(canvas, panel, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)


def add_card(tree, canvas, k, x, y):
    inner = CARD_W - 2 * PAD
    card = unreal.new_object(unreal.Border, tree, "Card%d" % k)  # fill colour and dim target: Lua sets both
    card.set_editor_property("brush_color", color(CLEAR))
    card.set_visibility(SELF_HIT_TEST_INVISIBLE)
    box = unreal.new_object(unreal.CanvasPanel, tree, "CardCanvas%d" % k)
    card.set_content(box)
    place(canvas, card, x, y, CARD_W, CARD_H)
    make_flat(tree, box, "CardTop%d" % k, CLEAR, 0, 0, CARD_W, 1)
    make_text(tree, box, "NameText%d" % k, "-", PAD, 10, 230, 26, size=18, rgba=WHITE)
    make_text(tree, box, "StatusText%d" % k, "", CARD_W - PAD - 100, 15, 100, 18, size=11, rgba=MUTED, spacing=1, align="right")
    make_text(tree, box, "SourceText%d" % k, "", PAD, 38, inner, 18, size=11, rgba=MUTED)
    for j in range(EFFECT_LINES):
        make_text(tree, box, "EffText%d_%d" % (k, j), "", PAD, 58 + 20 * j, inner, 20, size=13, rgba=SOFT)
    make_text(tree, box, "HintText%d" % k, "", PAD, 114, inner - 104, 34, size=11, rgba=MUTED, wrap=True)
    make_text(tree, box, "ActText%d" % k, "", CARD_W - PAD - 100, 112, 100, 26, size=18, rgba=WHITE, align="right")
    make_flat(tree, box, "ActUnder%d" % k, CLEAR, CARD_W - PAD - 100, 142, 100, 1)
    make_button(tree, box, "ActButton%d" % k, CARD_W - PAD - 120, 108, 120, 36)


def add_cards(tree, canvas):
    for k in range(CARDS):
        row, column = divmod(k, COLUMNS)
        x = PANEL_X + PANEL_PAD + column * (CARD_W + CARD_GAP)
        y = PANEL_Y + PANEL_PAD + row * (CARD_H + CARD_GAP)
        add_card(tree, canvas, k, x, y)


def add_dialog(tree, canvas):
    # The dialog comes last, so it lies on top. Everything is clear and empty until Lua opens it.
    make_flat(tree, canvas, "DlgShade", CLEAR, 0, 0, CANVAS_W, CANVAS_H)
    x = (CANVAS_W - DIALOG_W) // 2
    y = 170
    make_flat(tree, canvas, "DlgPanel", CLEAR, x, y, DIALOG_W, DIALOG_H)
    make_text(tree, canvas, "DlgTitle", "", x, y + 16, DIALOG_W, 30, size=22, rgba=WHITE, spacing=3, align="center")
    make_flat(tree, canvas, "DlgRule", CLEAR, x + (DIALOG_W - 200) // 2, y + 52, 200, 1)
    make_text(tree, canvas, "DlgQuestion", "", x + 20, y + 66, DIALOG_W - 40, 30, size=20, rgba=WHITE, align="center")
    for j in range(EFFECT_LINES):
        make_text(tree, canvas, "DlgEff%d" % j, "", x + 20, y + 108 + 26 * j, DIALOG_W - 40, 24, size=16, rgba=SOFT, align="center")
    make_text(tree, canvas, "DlgCost", "", x + 32, y + 196, DIALOG_W - 64, 44, size=15, rgba=GOLD, align="center", wrap=True)
    make_text(tree, canvas, "DlgCancelText", "", x + 90, y + 262, 150, 32, size=22, rgba=SOFT, align="center")
    make_text(tree, canvas, "DlgConfirmText", "", x + DIALOG_W - 240, y + 262, 150, 32, size=22, rgba=WHITE, align="center")
    make_flat(tree, canvas, "DlgConfirmUnder", CLEAR, x + DIALOG_W - 210, y + 294, 90, 1)
    make_button(tree, canvas, "DlgCancelButton", x + 90, y + 256, 150, 42)
    make_button(tree, canvas, "DlgConfirmButton", x + DIALOG_W - 240, y + 256, 150, 42)


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
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "LawsCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    add_filters(tree, canvas)
    add_panel(tree, canvas)
    add_cards(tree, canvas)
    make_text(tree, canvas, "NoticeText", "", 0, 652, CANVAS_W, 18, size=13, rgba=GOLD, align="center")
    add_dialog(tree, canvas)


def drop_graphs(bp):
    # The copied graphs refer to widgets that no longer exist.
    lib = unreal.BlueprintEditorLibrary
    graph = lib.find_event_graph(bp)
    if graph:
        lib.remove_graph(bp, graph)
    for name in LEFTOVER_FUNCTIONS:
        found = lib.find_graph(bp, name)
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
