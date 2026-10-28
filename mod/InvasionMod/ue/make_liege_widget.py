# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_LiegeContracts from a stock engine widget (same method as make_tech_widget.py).
# Change update-liege-tribute-to-contracts (#505): the liege window shows three contract cards, an active panel, the arms
# shipment button and a close button. The contracts are data (data/liege_contracts/contracts.json), but a pak asset is fixed,
# so the asset holds POOLS of controls. Lua fills, shows and hides them. Lua finds widgets by name and puts a
# WBP_ClickButton into each button Border (HarnessClickHooks).
# Names (card c = 0..2, objective item i = 0..1, reward item i = 0..2):
#   TextBlocks: TitleText, InfluenceText, SilverText, EmptyText, FooterText, ArmsInfoText, ActiveName, ActiveLine0, ActiveLine1, ActiveDays,
#               CardName<c>, CardQuote<c>, CardPenalty<c>, CardState<c>, ObjIcon<c>_<i>, ObjText<c>_<i>, RewIcon<c>_<i>, RewText<c>_<i>
#   Borders:    Card<c>, ObjItem<c>_<i>, RewItem<c>_<i>, ActivePanel
#   Buttons (Borders): PickButton0..2, CompleteButton, ArmsButton, CloseButton
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_LiegeContracts"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
CARDS, OBJ_ITEMS, REW_ITEMS = 3, 2, 3
CARD_WIDTH = 280
FONT_SIZE = 13
TITLE_SIZE = 18
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]
CARD_COLOR = unreal.LinearColor(0.15, 0.11, 0.07, 1.0)
ICON_COLOR = unreal.LinearColor(0.09, 0.07, 0.05, 1.0)
CLEAR = unreal.LinearColor(0, 0, 0, 0)


def log(msg):
    unreal.log("LIEGE: " + str(msg))


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def make_text(tree, name, text, size=FONT_SIZE, wrap=False):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    try:
        font = block.get_editor_property("font")
        font.set_editor_property("size", size)
        block.set_editor_property("font", font)
    except Exception as error:  # noqa: BLE001 - keep the default font when the editor API differs
        log("font size failed for %s: %s" % (name, error))
    if wrap:
        block.set_editor_property("auto_wrap_text", True)
    return block


def make_button(tree, name):
    # Lua puts a WBP_ClickButton into this border (spec 34): its OnClicked event is hookable, a Button here is not.
    slot = unreal.new_object(unreal.Border, tree, name)
    slot.set_editor_property("brush_color", CLEAR)  # a Border paints white by default
    return slot


def make_item(tree, item_name, icon_name, text_name):
    # An item: a clear Border (it carries the tooltip) around a letter box and an amount text.
    item = unreal.new_object(unreal.Border, tree, item_name)
    item.set_editor_property("brush_color", CLEAR)
    item.set_editor_property("padding", unreal.Margin(2, 2, 8, 2))
    row = unreal.new_object(unreal.HorizontalBox, tree, item_name + "Row")
    item.set_content(row)
    box = unreal.new_object(unreal.Border, tree, item_name + "Box")
    box.set_editor_property("brush_color", ICON_COLOR)
    box.set_editor_property("padding", unreal.Margin(8, 4, 8, 4))
    box.set_content(make_text(tree, icon_name, "?"))
    row.add_child(box)
    spacer = unreal.new_object(unreal.Border, tree, item_name + "Pad")
    spacer.set_editor_property("brush_color", CLEAR)
    spacer.set_editor_property("padding", unreal.Margin(6, 4, 0, 0))
    spacer.set_content(make_text(tree, text_name, "-"))
    row.add_child(spacer)
    return item


def make_card(tree, c):
    card = unreal.new_object(unreal.Border, tree, "Card%d" % c)
    card.set_editor_property("brush_color", CARD_COLOR)
    card.set_editor_property("padding", unreal.Margin(12, 10, 12, 10))
    size = unreal.new_object(unreal.SizeBox, tree, "CardSize%d" % c)
    size.set_editor_property("width_override", CARD_WIDTH)
    card.set_content(size)
    column = unreal.new_object(unreal.VerticalBox, tree, "CardColumn%d" % c)
    size.set_content(column)
    column.add_child(make_text(tree, "CardName%d" % c, "-"))
    column.add_child(make_text(tree, "CardQuote%d" % c, "", wrap=True))
    column.add_child(make_text(tree, "ObjLabel%d" % c, "OBJECTIVE"))
    for i in range(OBJ_ITEMS):
        column.add_child(make_item(tree, "ObjItem%d_%d" % (c, i), "ObjIcon%d_%d" % (c, i), "ObjText%d_%d" % (c, i)))
    column.add_child(make_text(tree, "RewLabel%d" % c, "REWARDS"))
    for i in range(REW_ITEMS):
        column.add_child(make_item(tree, "RewItem%d_%d" % (c, i), "RewIcon%d_%d" % (c, i), "RewText%d_%d" % (c, i)))
    column.add_child(make_text(tree, "CardPenalty%d" % c, ""))
    column.add_child(make_button(tree, "PickButton%d" % c))
    column.add_child(make_text(tree, "CardState%d" % c, ""))
    return card


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", unreal.LinearColor(0.05, 0.04, 0.03, 0.9))
    panel.set_editor_property("padding", unreal.Margin(16, 12, 16, 12))
    seed.add_child(panel)
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    panel.set_content(column)
    header = unreal.new_object(unreal.HorizontalBox, tree, "HeaderRow")
    for name, text in (("TitleText", "Contracts of the Liege"), ("InfluenceText", "Influence: 0"), ("SilverText", "Silver: 0")):
        pad = unreal.new_object(unreal.Border, tree, name + "Pad")
        pad.set_editor_property("brush_color", CLEAR)
        pad.set_editor_property("padding", unreal.Margin(0, 0, 32, 8))
        pad.set_content(make_text(tree, name, text, TITLE_SIZE if name == "TitleText" else FONT_SIZE))
        header.add_child(pad)
    column.add_child(header)
    column.add_child(make_text(tree, "EmptyText", ""))
    cards = unreal.new_object(unreal.HorizontalBox, tree, "CardsRow")
    for c in range(CARDS):
        gap = unreal.new_object(unreal.Border, tree, "CardGap%d" % c)
        gap.set_editor_property("brush_color", CLEAR)
        gap.set_editor_property("padding", unreal.Margin(0, 0, 12, 0))
        gap.set_content(make_card(tree, c))
        cards.add_child(gap)
    column.add_child(cards)
    active = unreal.new_object(unreal.Border, tree, "ActivePanel")
    active.set_editor_property("brush_color", unreal.LinearColor(0.11, 0.085, 0.055, 1.0))
    active.set_editor_property("padding", unreal.Margin(12, 8, 12, 8))
    active_column = unreal.new_object(unreal.VerticalBox, tree, "ActiveColumn")
    active.set_content(active_column)
    for name, text in (("ActiveName", "-"), ("ActiveLine0", ""), ("ActiveLine1", ""), ("ActiveDays", "")):
        active_column.add_child(make_text(tree, name, text))
    active_column.add_child(make_button(tree, "CompleteButton"))
    column.add_child(active)
    column.add_child(make_text(tree, "FooterText", ""))
    column.add_child(make_text(tree, "ArmsInfoText", "Arms shipment"))
    column.add_child(make_button(tree, "ArmsButton"))
    column.add_child(make_button(tree, "CloseButton"))


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
