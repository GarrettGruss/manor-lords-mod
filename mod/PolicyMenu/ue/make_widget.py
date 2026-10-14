# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_PolicyMenu from a stock engine widget.
# Why a copy: the WidgetTree root widget is a protected property, so Python
# cannot set it on a new Widget Blueprint. A copy already has a root.
# The menu has a title and SLOT_COUNT policy buttons. Lua fills the label of each
# button and hides the unused ones. Lua finds the widgets by name (FindAllOf).
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_PolicyMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
SLOT_COUNT = 20
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]


def log(msg):
    unreal.log("PMENU: " + str(msg))


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def find_root(bp):
    tree = unreal.find_object(bp, "WidgetTree")
    seed = unreal.find_object(tree, SEED_WIDGET)
    root = seed.get_editor_property("slot").get_outer()
    log("root=" + root.get_path_name())
    return tree, root, seed


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    seed.add_child(column)
    title = unreal.new_object(unreal.TextBlock, tree, "TitleText")
    title.set_editor_property("text", "Policies")
    column.add_child(title)
    for i in range(SLOT_COUNT):
        button = unreal.new_object(unreal.Button, tree, "PolicyButton%d" % i)
        label = unreal.new_object(unreal.TextBlock, tree, "PolicyLabel%d" % i)
        label.set_editor_property("text", "-")
        button.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
        button.add_child(label)
        column.add_child(button)


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
    tree, root, seed = find_root(bp)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
