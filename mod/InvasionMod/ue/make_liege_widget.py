# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_LiegeTribute from a stock engine widget (same method as make_raid_widget.py).
# The menu has a title, an influence text, a tribute button, an arms shipment button (change add-scenario-start-kit) and a close button.
# Lua puts a WBP_ClickButton into each Border (HarnessClickHooks) and fills the texts. Lua finds widgets by name.
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_LiegeTribute"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]
TEXTS = [("TitleText", "Liege"), ("InfluenceText", "Influence: 0"), ("TributeInfoText", "Tribute: 200 silver"), ("ArmsInfoText", "Arms shipment")]
BUTTONS = ["TributeButton", "ArmsButton", "CloseButton"]


def log(msg):
    unreal.log("LIEGE: " + str(msg))


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", unreal.LinearColor(0.05, 0.04, 0.03, 0.85))
    panel.set_editor_property("padding", unreal.Margin(16, 12, 16, 12))
    seed.add_child(panel)
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    panel.set_content(column)
    for name, text in TEXTS:
        block = unreal.new_object(unreal.TextBlock, tree, name)
        block.set_editor_property("text", text)
        column.add_child(block)
    for name in BUTTONS:
        slot = unreal.new_object(unreal.Border, tree, name)
        slot.set_editor_property("brush_color", unreal.LinearColor(0, 0, 0, 0))  # a Border paints white by default
        column.add_child(slot)


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
