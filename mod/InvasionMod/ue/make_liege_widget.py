# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_LiegeContracts from a stock engine widget (same method as make_tech_widget.py).
# Change update-liege-contracts-window-style (#538): the liege window follows the mockup liege-contracts-game-style.html (the look of the
# game's Diplomacy window): near-black background, centred title with a thin gold rule, one countdown line with gold numbers, one dark grey
# panel with three rows (Small, Medium, Large) of a tier box and three cards, serif text, plain-text Fulfil. No Close in the widget (the menu
# framework draws the game's Close at the bottom middle).
# The contracts are data (data/liege_contracts/contracts.json), but a pak asset is fixed, so the asset holds a POOL of 9 cards on ONE
# canvas. Lua fills, shows and hides them. Lua finds widgets by name and puts a WBP_ClickButton into each button Border (HarnessClickHooks).
# Game assets (notes/fonts-textures.md): the font and the panel texture are referenced by their game path. The editor has no game content,
# so empty stub assets are made at the same paths; the stubs are never copied into the pak (copy only WBP_LiegeContracts.*).
# Names (row r = 0..2 for Small, Medium, Large; card c = 0..2, key = r_c):
#   TextBlocks: TitleText, RemainLabel, RemainValue, RefreshLabel, RefreshValue, NoticeText, TierName<r>, TierCap<r>, TierCount<r>,
#               ReqLabel<key>, ReqText<key>, HaveText<key>, HaveMiss<key>, RewLabel<key>, RewText<key>, FulfilledText<key>
#   Borders:    Card<key> (also the dim target), FulfilButton<key> (button borders)
import os
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_LiegeContracts"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
FONT_PATH = os.environ.get("LIEGE_FONT", "Game/UWG/fonts/CombinedFont_Mikadan")  # no leading slash (Git Bash rewrites it)  # a game font path, or empty for the engine font (notes/fonts-textures.md)
TYPEFACE = os.environ.get("LIEGE_TYPEFACE", "")  # the typeface name inside a composite font
PANEL_TEXTURE_PATH = os.environ.get("LIEGE_TEXTURE", "")  # a game texture path, or empty for a flat colour
ROWS, CARDS = 3, 3
CANVAS_W, CANVAS_H = 1152, 654
PANEL_X, PANEL_Y, PANEL_W = 16, 122, 1120
PANEL_PAD, ROW_H, ROW_GAP = 14, 150, 12
TIER_W, TIER_GAP = 150, 12
CARD_W = 302
CARD_GAP = 12
PANEL_H = 2 * PANEL_PAD + ROWS * ROW_H + (ROWS - 1) * ROW_GAP
PAD = 16                      # inside a card
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]

GOLD = (0.91, 0.78, 0.48, 1)
WHITE = (0.95, 0.93, 0.89, 1)
SOFT = (0.79, 0.76, 0.69, 1)
MUTED = (0.66, 0.63, 0.56, 1)
RED = (0.69, 0.44, 0.36, 1)
RULE = (0.61, 0.52, 0.33, 1)
BACKGROUND = (0.055, 0.055, 0.05, 1)
PANEL = (0.26, 0.25, 0.225, 1)  # flat colour; a texture would multiply it (grungeTiling is too dark, notes/fonts-textures.md)
TIER_BG = (0.06, 0.06, 0.05, 0.5)
CARD_BG = (0.08, 0.075, 0.065, 0.55)
CARD_TOP = (0.29, 0.275, 0.24, 1)
DIAMOND = (0.56, 0.53, 0.47, 1)
CLEAR = (0, 0, 0, 0)
HIT_TEST_INVISIBLE = unreal.SlateVisibility.HIT_TEST_INVISIBLE
SELF_HIT_TEST_INVISIBLE = unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE

FONT = None
PANEL_TEXTURE = None


def log(msg):
    unreal.log("LIEGE: " + str(msg))


def color(rgba):
    # The values above are the sRGB colours of the mockup; a LinearColor needs linear values (0.055 linear shows as 0.26).
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
    global FONT, PANEL_TEXTURE, FONT_PATH, PANEL_TEXTURE_PATH
    FONT_PATH = "/" + FONT_PATH.lstrip("/") if FONT_PATH else ""
    PANEL_TEXTURE_PATH = "/" + PANEL_TEXTURE_PATH.lstrip("/") if PANEL_TEXTURE_PATH else ""
    try:
        if FONT_PATH:
            FONT = make_stub(FONT_PATH, unreal.Font, unreal.FontFactory())
    except Exception as error:  # noqa: BLE001 - fallback: the engine font stays
        log("font stub failed (fallback: engine font): %s" % error)
    try:
        if PANEL_TEXTURE_PATH:
            PANEL_TEXTURE = make_stub(PANEL_TEXTURE_PATH, unreal.Texture2D, unreal.Texture2DFactoryNew())
    except Exception as error:  # noqa: BLE001 - fallback: flat panel colour
        log("texture stub failed (fallback: flat colour): %s" % error)
    log("font=%s texture=%s" % (FONT, PANEL_TEXTURE))


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


def new_text(tree, name, text, size=16, rgba=WHITE, spacing=0, center=False, wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        style_text(block, size, rgba, spacing, center, wrap)
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
    border = make_flat(tree, canvas, name, DIAMOND, x, y, 6, 6)
    try:
        border.set_editor_property("render_transform", unreal.WidgetTransform(angle=45))
    except Exception as error:  # noqa: BLE001 - fallback: a square marker
        log("diamond rotation failed: %s" % error)
    return border


def make_button(tree, canvas, name, x, y, w, h):
    # Lua puts a WBP_ClickButton into this border (spec 34): its OnClicked event is hookable, a Button here is not.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", color(CLEAR))  # a Border paints white by default
    place(canvas, border, x, y, w, h)
    return border


def make_line(tree, canvas, name, first, second, x, y, w):
    # Two text blocks side by side (white label, gold value). Lua writes both.
    row = unreal.new_object(unreal.HorizontalBox, tree, name)
    slot = row.add_child(first)
    slot.set_padding(unreal.Margin(0, 0, 6, 0))
    row.add_child(second)
    row.set_visibility(SELF_HIT_TEST_INVISIBLE)
    place(canvas, row, x, y, w, 24)


def add_header(tree, canvas):
    make_text(tree, canvas, "TitleText", "CONTRACTS OF THE LIEGE", 0, 18, CANVAS_W, 30, size=22, rgba=WHITE, spacing=5, center=True)
    make_flat(tree, canvas, "TitleRule", RULE, (CANVAS_W - 300) // 2, 54, 300, 1)
    bar = unreal.new_object(unreal.Border, tree, "CountdownBar")
    bar.set_editor_property("brush_color", color(CLEAR))
    bar.set_visibility(HIT_TEST_INVISIBLE)
    bar.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
    row = unreal.new_object(unreal.HorizontalBox, tree, "CountdownRow")
    parts = [("RemainLabel", "Time to fulfil contracts:", SOFT, 6), ("RemainValue", "-", GOLD, 56),
             ("RefreshLabel", "Contracts refresh:", SOFT, 6), ("RefreshValue", "In spring", GOLD, 0)]
    for name, text, rgba, gap in parts:
        slot = row.add_child(new_text(tree, name, text, size=15, rgba=rgba))
        slot.set_padding(unreal.Margin(0, 0, gap, 0))
    bar.set_content(row)
    place(canvas, bar, 0, 66, CANVAS_W, 30)
    make_text(tree, canvas, "NoticeText", "", 0, 96, CANVAS_W, 20, size=13, rgba=GOLD, center=True)


def add_panel(tree, canvas):
    panel = unreal.new_object(unreal.Border, tree, "TierPanel")
    panel.set_editor_property("brush_color", color(PANEL))
    panel.set_visibility(HIT_TEST_INVISIBLE)
    if PANEL_TEXTURE is not None:
        try:
            brush = panel.get_editor_property("background")
            brush.set_editor_property("resource_object", PANEL_TEXTURE)
            brush.set_editor_property("draw_as", unreal.SlateBrushDrawType.IMAGE)
            brush.set_editor_property("tiling", unreal.SlateBrushTileType.BOTH)
            panel.set_editor_property("background", brush)
        except Exception as error:  # noqa: BLE001
            log("panel brush failed (flat colour): %s" % error)
    place(canvas, panel, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)


def add_tier_box(tree, canvas, r, x, y):
    make_flat(tree, canvas, "TierBox%d" % r, TIER_BG, x, y, TIER_W, ROW_H)
    make_text(tree, canvas, "TierName%d" % r, "-", x, y + 26, TIER_W, 34, size=20, rgba=WHITE, center=True)
    make_flat(tree, canvas, "TierRule%d" % r, RULE, x + (TIER_W - 90) // 2, y + 66, 90, 1)
    make_text(tree, canvas, "TierCap%d" % r, "Fulfilled", x, y + 76, TIER_W, 20, size=11, rgba=MUTED, center=True)
    make_text(tree, canvas, "TierCount%d" % r, "0 / 1", x, y + 98, TIER_W, 34, size=18, rgba=GOLD, center=True)


def add_card(tree, canvas, r, c, x, y):
    key = "%d_%d" % (r, c)
    inner = CARD_W - 2 * PAD
    card = unreal.new_object(unreal.Border, tree, "Card" + key)  # also the dim target: Lua sets its render opacity
    card.set_editor_property("brush_color", color(CARD_BG))
    card.set_visibility(SELF_HIT_TEST_INVISIBLE)
    box = unreal.new_object(unreal.CanvasPanel, tree, "CardCanvas" + key)
    card.set_content(box)
    place(canvas, card, x, y, CARD_W, ROW_H)
    make_flat(tree, box, "CardTop" + key, CARD_TOP, 0, 0, CARD_W, 1)
    make_diamond(tree, box, "DiamondReq" + key, PAD, 22)
    make_line(tree, box, "ReqLine" + key, new_text(tree, "ReqLabel" + key, "", size=14), new_text(tree, "ReqText" + key, "-", size=13, rgba=GOLD, spacing=0),
              PAD + 20, 12, inner - 20)
    make_text(tree, box, "HaveText" + key, "-", PAD + 20, 42, inner - 20, 22, size=12, rgba=SOFT)
    make_text(tree, box, "HaveMiss" + key, "", PAD + 20, 42, inner - 20, 22, size=12, rgba=RED)
    make_diamond(tree, box, "DiamondRew" + key, PAD, 80)
    make_line(tree, box, "RewLine" + key, new_text(tree, "RewLabel" + key, "", size=14), new_text(tree, "RewText" + key, "-", size=13, rgba=GOLD, spacing=0),
              PAD + 20, 70, inner - 20)
    make_text(tree, box, "FulfilledText" + key, "", PAD, ROW_H - 42, inner, 30, size=17, rgba=GOLD)
    make_button(tree, box, "FulfilButton" + key, PAD, ROW_H - 42, inner, 34)


def add_rows(tree, canvas):
    for r in range(ROWS):
        y = PANEL_Y + PANEL_PAD + r * (ROW_H + ROW_GAP)
        add_tier_box(tree, canvas, r, PANEL_X + PANEL_PAD, y)
        for c in range(CARDS):
            x = PANEL_X + PANEL_PAD + TIER_W + TIER_GAP + c * (CARD_W + CARD_GAP)
            add_card(tree, canvas, r, c, x, y)


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
    background = unreal.new_object(unreal.Border, tree, "MenuPanel")
    background.set_editor_property("brush_color", color(BACKGROUND))
    seed.add_child(background)
    box = unreal.new_object(unreal.SizeBox, tree, "MenuBox")
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", CANVAS_H)
    background.set_content(box)
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "LiegeCanvas")
    box.set_content(canvas)
    add_header(tree, canvas)
    add_panel(tree, canvas)
    add_rows(tree, canvas)


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
