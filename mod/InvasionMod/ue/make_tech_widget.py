# Runs inside UnrealEditor-Cmd (-ExecutePythonScript). Makes /Game/HarnessMod/WBP_TechTreeMenu from a stock engine widget.
# Same method as make_raid_widget.py. The tree is data driven (data/tech_tree/tree.json), but a pak asset is fixed.
# So the asset holds POOLS of controls on ONE canvas (layout of change update-tech-tree-widget-layout, the mockup scaled to 0.8, a little taller for the law rows: 1152 x 704).
# Lua shows, hides, labels, colours and moves the pool entries from the JSON data (features/tech_tree_widget/init.lua).
# Fixed parts: HeaderBg, TitleText, PicksText, CloseButton, ColBand0..3, ColHead0..3, RowName0..2, RowStatus0..2, PathButton0..1,
#   LawsStripBg, StripTitle, StripCount, StripPlaceBg0..1, StripName0..1, StripRepeal0..1, FooterBg, FooterMsg, FooterFixed.
# Pools that Lua moves (NODE_COUNT entries each): NodeButton, RingBg, RingLetter, CardLaw (text), LawButton. LinkBg0..LINK_COUNT-1 are the links.
# A button is a Border (Lua puts a WBP_ClickButton into it). Flat colours only: no rounded corners, glow or SVG (design.md).
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_TechTreeMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
PATH_BUTTON_COUNT = 2
NODE_COUNT = 16
LINK_COUNT = 6
STRIP_PLACES = 2
CANVAS_W, CANVAS_H = 1152, 704
CARD_W, CARD_H = 216, 150
LAW_ROW_H = 48  # the bottom of a card: the law name and its button; the click area of the card is above
ORIGIN_X, ORIGIN_Y = 160, 100
STEP_X, STEP_Y = 248, 160
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.89, 0.76, 0.48, 1)
TEXT = (0.92, 0.87, 0.78, 1)
MUTED = (0.72, 0.66, 0.53, 1)
PANEL = (0.13, 0.10, 0.07, 1)
BAND_A = (0.09, 0.07, 0.05, 1)
BAND_B = (0.11, 0.085, 0.055, 1)
STRIP = (0.115, 0.085, 0.055, 1)
PLACE = (0.2, 0.15, 0.09, 1)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE


def log(msg):
    unreal.log("TMENU: " + str(msg))


def color(rgba):
    return unreal.LinearColor(*rgba)


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def find_tree(bp):
    tree = unreal.find_object(bp, "WidgetTree")
    seed = unreal.find_object(tree, SEED_WIDGET)
    return tree, seed


def place(canvas, widget, x, y, w, h):
    slot = canvas.add_child_to_canvas(widget)
    slot.set_position(unreal.Vector2D(x, y))
    slot.set_size(unreal.Vector2D(w, h))
    slot.set_auto_size(False)
    return slot


def make_text(tree, canvas, name, text, x, y, w, h, size=14, rgba=TEXT, wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        font = block.get_editor_property("font")
        font.size = size
        block.set_editor_property("font", font)
        block.set_editor_property("color_and_opacity", unreal.SlateColor(color(rgba)))
        if wrap:
            block.set_editor_property("auto_wrap_text", True)
        block.set_visibility(SELF_HIT_TEST_INVISIBLE)
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


def add_header(tree, canvas):
    make_flat(tree, canvas, "HeaderBg", PANEL, 0, 0, CANVAS_W, 67)
    make_text(tree, canvas, "TitleText", "Charters of the Realm", 26, 14, 520, 40, size=26, rgba=GOLD)
    make_text(tree, canvas, "PicksText", "Tech picks", 590, 20, 430, 30, size=18)
    make_button(tree, canvas, "CloseButton", 1040, 14, 90, 38)


def add_columns(tree, canvas):
    for i in range(4):
        x = ORIGIN_X - 20 + i * STEP_X
        make_flat(tree, canvas, "ColBand%d" % i, BAND_A if i % 2 == 0 else BAND_B, x, 67, STEP_X, 513)
    for i in range(4):
        make_text(tree, canvas, "ColHead%d" % i, "-", ORIGIN_X + i * STEP_X, 72, CARD_W, 24, size=16, rgba=GOLD)


def add_rows(tree, canvas):
    for r in range(3):
        y = ORIGIN_Y + r * STEP_Y
        make_text(tree, canvas, "RowName%d" % r, "-", 20, y, 130, 26, size=18)
        make_text(tree, canvas, "RowStatus%d" % r, "-", 20, y + 28, 130, 56, size=12, rgba=MUTED, wrap=True)
    for i in range(PATH_BUTTON_COUNT):
        make_button(tree, canvas, "PathButton%d" % i, 20, ORIGIN_Y + i * STEP_Y + 88, 124, 32)


def add_cards(tree, canvas):
    for i in range(LINK_COUNT):
        make_flat(tree, canvas, "LinkBg%d" % i, (0.23, 0.17, 0.1, 1), ORIGIN_X + CARD_W, ORIGIN_Y + (CARD_H - LAW_ROW_H) // 2, STEP_X - CARD_W, 4)
    for i in range(NODE_COUNT):
        make_button(tree, canvas, "NodeButton%d" % i, ORIGIN_X, ORIGIN_Y, CARD_W, CARD_H - LAW_ROW_H)
    for i in range(NODE_COUNT):
        make_flat(tree, canvas, "RingBg%d" % i, (0.35, 0.28, 0.16, 1), ORIGIN_X, ORIGIN_Y, 26, 26)
    for i in range(NODE_COUNT):
        make_text(tree, canvas, "RingLetter%d" % i, "-", ORIGIN_X, ORIGIN_Y, 26, 24, size=16, rgba=(0.09, 0.07, 0.05, 1))
    for i in range(NODE_COUNT):
        make_text(tree, canvas, "CardLaw%d" % i, "-", ORIGIN_X, ORIGIN_Y, CARD_W - 16, 18, size=11, rgba=GOLD)
    for i in range(NODE_COUNT):
        make_button(tree, canvas, "LawButton%d" % i, ORIGIN_X, ORIGIN_Y, 66, 24)


def add_strip(tree, canvas):
    make_flat(tree, canvas, "LawsStripBg", STRIP, 19, 586, 1114, 66)
    make_text(tree, canvas, "StripTitle", "Laws in force", 30, 592, 150, 26, size=18, rgba=GOLD)
    make_text(tree, canvas, "StripCount", "-", 30, 620, 140, 24, size=15)
    for i in range(STRIP_PLACES):
        x = 180 + i * 470
        make_flat(tree, canvas, "StripPlaceBg%d" % i, PLACE, x, 590, 460, 58)
        make_text(tree, canvas, "StripName%d" % i, "-", x + 10, 594, 340, 50, size=13)
        make_button(tree, canvas, "StripRepeal%d" % i, x + 356, 602, 94, 32)


def add_footer(tree, canvas):
    make_flat(tree, canvas, "FooterBg", PANEL, 0, 660, CANVAS_W, 44)
    make_text(tree, canvas, "FooterMsg", "-", 26, 670, 640, 26, size=15)
    make_text(tree, canvas, "FooterFixed", "-", 670, 672, 470, 24, size=13, rgba=MUTED)


def center_seed(seed):
    # The stock widget puts the seed at 58 percent of the viewport height (anchors 0 / 0.583). Centre the window instead, at its own size.
    slot = seed.get_editor_property("slot")
    slot.set_anchors(unreal.Anchors(unreal.Vector2D(0.5, 0.5), unreal.Vector2D(0.5, 0.5)))
    slot.set_alignment(unreal.Vector2D(0.5, 0.5))
    slot.set_offsets(unreal.Margin(0, 0, CANVAS_W, CANVAS_H))


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    center_seed(seed)
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", unreal.LinearColor(0.09, 0.07, 0.05, 1))
    seed.add_child(panel)
    box = unreal.new_object(unreal.SizeBox, tree, "MenuBox")
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", CANVAS_H)
    panel.set_content(box)
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "TreeCanvas")
    box.set_content(canvas)
    add_columns(tree, canvas)
    add_rows(tree, canvas)
    add_cards(tree, canvas)
    add_strip(tree, canvas)
    add_header(tree, canvas)
    add_footer(tree, canvas)


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
    bp = copy_source()
    tree, seed = find_tree(bp)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
