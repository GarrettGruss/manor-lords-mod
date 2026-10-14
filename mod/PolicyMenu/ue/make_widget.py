# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_PolicyMenu from a stock engine widget.
# Why a copy: the WidgetTree root widget is a protected property, so Python
# cannot set it on a new Widget Blueprint. A copy already has a root.
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_PolicyMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
POLICIES = ["Strict fasting", "Tithe relief", "Free pasture"]


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


def add_menu(tree, root, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    box = seed
    title = unreal.new_object(unreal.TextBlock, tree, "TitleText")
    title.set_editor_property("text", "Policy menu")
    box.add_child(title)
    for i, name in enumerate(POLICIES):
        button = unreal.new_object(unreal.Button, tree, "PolicyButton%d" % i)
        label = unreal.new_object(unreal.TextBlock, tree, "PolicyLabel%d" % i)
        label.set_editor_property("text", name)
        button.add_child(label)
        box.add_child(button)


def drop_graphs(bp):
    # The copied graphs refer to widgets that no longer exist.
    lib = unreal.BlueprintEditorLibrary
    graph = lib.find_event_graph(bp)
    log("event graph=%s" % graph)
    if graph:
        lib.remove_graph(bp, graph)


def main():
    bp = copy_source()
    tree, root, seed = find_root(bp)
    add_menu(tree, root, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
