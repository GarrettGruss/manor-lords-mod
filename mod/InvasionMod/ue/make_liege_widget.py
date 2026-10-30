# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_LiegeContracts from a stock engine widget (same method as make_tech_widget.py).
# Change update-liege-contracts-tiers (#533): the liege window follows the mockup liege-contracts-tiers.html: a top bar (title and two
# countdowns), a notice line, three rows (Small, Medium, Large) with a tier box and three contract cards each, and a full-width Close button.
# The contracts are data (data/liege_contracts/contracts.json), but a pak asset is fixed, so the asset holds a POOL of 9 cards on ONE
# canvas. Lua fills, shows and hides them. Lua finds widgets by name and puts a WBP_ClickButton into each button Border (HarnessClickHooks).
# Names (row r = 0..2 for Small, Medium, Large; card c = 0..2):
#   TextBlocks: TitleText, RemainText, RefreshText, NoticeText, TierName<r>, TierCount<r>,
#               ReqLabel<r>_<c>, ReqText<r>_<c>, HaveText<r>_<c>, RewLabel<r>_<c>, RewText<r>_<c>
#   Borders:    TierBox<r>, Card<r>_<c>
#   Buttons (Borders): FulfilButton<r>_<c>, CloseButton
# No arms shipment button (removed by this change).
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_LiegeContracts"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
ROWS, CARDS = 3, 3
CANVAS_W, CANVAS_H = 1152, 704
HEADER_H = 60
NOTICE_Y = 64
ROWS_Y, ROW_H, ROW_GAP = 96, 170, 8
TIER_X, TIER_W = 16, 160
CARD_X0, CARD_W, CARD_GAP = 192, 306, 12
CLOSE_Y, CLOSE_H = 640, 56
PAD = 14                      # inside a card
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.89, 0.76, 0.48, 1)
TEXT = (0.92, 0.87, 0.78, 1)
MUTED = (0.72, 0.66, 0.53, 1)
PANEL = (0.09, 0.07, 0.05, 1)
HEADER = (0.13, 0.10, 0.07, 1)
TIER_BG = (0.115, 0.085, 0.055, 1)
CARD_BG = (0.15, 0.115, 0.07, 1)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE


def log(msg):
    unreal.log("LIEGE: " + str(msg))


def color(rgba):
    return unreal.LinearColor(*rgba)


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
    make_flat(tree, canvas, "HeaderBg", HEADER, 0, 0, CANVAS_W, HEADER_H)
    make_text(tree, canvas, "TitleText", "Contracts of the Liege", 24, 14, 340, 36, size=24, rgba=GOLD)
    make_text(tree, canvas, "RemainText", "Time to fulfil contracts: -", 384, 6, 740, 24, size=14)
    make_text(tree, canvas, "RefreshText", "Contracts refresh: In spring", 384, 32, 740, 24, size=14)
    make_text(tree, canvas, "NoticeText", "", 24, NOTICE_Y, 1100, 24, size=15, rgba=GOLD)


def add_tier_box(tree, canvas, r, y):
    make_flat(tree, canvas, "TierBox%d" % r, TIER_BG, TIER_X, y, TIER_W, ROW_H)
    make_text(tree, canvas, "TierName%d" % r, "-", TIER_X + 16, y + 34, TIER_W - 24, 34, size=26, rgba=GOLD)
    make_text(tree, canvas, "TierCap%d" % r, "FULFILLED", TIER_X + 16, y + 82, TIER_W - 24, 18, size=12, rgba=MUTED)
    make_text(tree, canvas, "TierCount%d" % r, "0 / 1", TIER_X + 16, y + 102, TIER_W - 24, 34, size=26)


def add_card(tree, canvas, r, c, y):
    key = "%d_%d" % (r, c)
    x = CARD_X0 + c * (CARD_W + CARD_GAP)
    inner = CARD_W - 2 * PAD
    make_flat(tree, canvas, "Card" + key, CARD_BG, x, y, CARD_W, ROW_H)
    make_text(tree, canvas, "ReqLabel" + key, "", x + PAD, y + 8, inner, 16, size=11, rgba=MUTED)
    make_text(tree, canvas, "ReqText" + key, "-", x + PAD, y + 24, inner, 24, size=17)
    make_text(tree, canvas, "HaveText" + key, "-", x + PAD, y + 50, inner, 20, size=14, rgba=MUTED)
    make_text(tree, canvas, "RewLabel" + key, "", x + PAD, y + 78, inner, 16, size=11, rgba=MUTED)
    make_text(tree, canvas, "RewText" + key, "-", x + PAD, y + 94, inner, 24, size=17, rgba=GOLD)
    make_button(tree, canvas, "FulfilButton" + key, x + PAD, y + 126, inner, 36)


def add_rows(tree, canvas):
    for r in range(ROWS):
        y = ROWS_Y + r * (ROW_H + ROW_GAP)
        add_tier_box(tree, canvas, r, y)
        for c in range(CARDS):
            add_card(tree, canvas, r, c, y)


def add_footer(tree, canvas):
    make_button(tree, canvas, "CloseButton", 16, CLOSE_Y, CANVAS_W - 32, CLOSE_H)


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
    panel.set_editor_property("brush_color", color(PANEL))
    seed.add_child(panel)
    box = unreal.new_object(unreal.SizeBox, tree, "MenuBox")
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", CANVAS_H)
    panel.set_content(box)
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "LiegeCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    add_rows(tree, canvas)
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
    tree = unreal.find_object(bp, "WidgetTree")
    seed = unreal.find_object(tree, SEED_WIDGET)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
