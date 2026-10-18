# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_RaidMenu from a stock engine widget (same method as mod/PolicyMenu/ue/make_widget.py).
# Why a copy: the WidgetTree root widget is a protected property, so Python cannot set it on a new Widget Blueprint.
# The menu has a title, LINE_COUNT text lines (RaidLine0..) and BUTTON_COUNT difficulty buttons (DifficultyButton0.. with
# DifficultyLabel0..). Lua fills the texts and polls the buttons. Lua finds the widgets by name (FindAllOf).
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_RaidMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
LINE_COUNT = 5
BUTTON_COUNT = 3
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]


def log(msg):
    unreal.log("RMENU: " + str(msg))


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


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", unreal.LinearColor(0.05, 0.04, 0.03, 0.85))
    panel.set_editor_property("padding", unreal.Margin(16, 12, 16, 12))
    seed.add_child(panel)
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    panel.set_content(column)
    title = unreal.new_object(unreal.TextBlock, tree, "TitleText")
    title.set_editor_property("text", "Raids")
    column.add_child(title)
    for i in range(LINE_COUNT):
        line = unreal.new_object(unreal.TextBlock, tree, "RaidLine%d" % i)
        line.set_editor_property("text", "-")
        column.add_child(line)
    for i in range(BUTTON_COUNT):
        # Lua puts a WBP_ClickButton into this border (spec 34): its OnClicked event is hookable, a Button here is not.
        column.add_child(unreal.new_object(unreal.Border, tree, "DifficultyButton%d" % i))


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
    bp = copy_source()
    tree, seed = find_tree(bp)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
