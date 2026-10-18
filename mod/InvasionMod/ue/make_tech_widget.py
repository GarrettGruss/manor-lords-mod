# Runs inside UnrealEditor-Cmd (-ExecutePythonScript). Makes /Game/HarnessMod/WBP_TechTreeMenu from a stock engine widget.
# Same method as make_raid_widget.py. The tree is data driven (data/tech_tree/tree.json), but a pak asset is fixed.
# So the asset holds a POOL of NODE_COUNT node buttons on a canvas. Lua shows, hides, labels and moves them from the JSON data.
# Laws (M12.05): LawsLine0, LawButton0.. (+LawLabel0..). Names: TitleText, TechLine0.., PathButton0.. (+PathLabel0..), TreeCanvas, NodeButton0.. (+NodeLabel0..).
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_TechTreeMenu"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
LINE_COUNT = 3
PATH_BUTTON_COUNT = 2
NODE_COUNT = 16
LAW_COUNT = 3
CANVAS_W, CANVAS_H = 760, 240
NODE_W, NODE_H = 170, 44
GRID_STEP_X, GRID_STEP_Y = 180, 60
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]


def log(msg):
    unreal.log("TMENU: " + str(msg))


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


def make_text(tree, name, text):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    return block


def make_button(tree, button_name, label_name):
    # Lua puts a WBP_ClickButton into this border (spec 34): its OnClicked event is hookable, a Button here is not.
    return unreal.new_object(unreal.Border, tree, button_name)


def add_path_row(tree, column):
    row = unreal.new_object(unreal.HorizontalBox, tree, "PathRow")
    for i in range(PATH_BUTTON_COUNT):
        row.add_child(make_button(tree, "PathButton%d" % i, "PathLabel%d" % i))
    column.add_child(row)


def add_tree_canvas(tree, column):
    box = unreal.new_object(unreal.SizeBox, tree, "TreeBox")
    box.set_editor_property("width_override", CANVAS_W)
    box.set_editor_property("height_override", CANVAS_H)
    canvas = unreal.new_object(unreal.CanvasPanel, tree, "TreeCanvas")
    box.set_content(canvas)
    for i in range(NODE_COUNT):
        slot = canvas.add_child_to_canvas(make_button(tree, "NodeButton%d" % i, "NodeLabel%d" % i))
        slot.set_position(unreal.Vector2D((i % 4) * GRID_STEP_X, (i // 4) * GRID_STEP_Y))
        slot.set_size(unreal.Vector2D(NODE_W, NODE_H))
    column.add_child(box)


def add_law_row(tree, column):
    column.add_child(make_text(tree, "LawsLine0", "-"))
    row = unreal.new_object(unreal.HorizontalBox, tree, "LawRow")
    for i in range(LAW_COUNT):
        row.add_child(make_button(tree, "LawButton%d" % i, "LawLabel%d" % i))
    column.add_child(row)


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", unreal.LinearColor(0.05, 0.04, 0.03, 0.85))
    panel.set_editor_property("padding", unreal.Margin(16, 12, 16, 12))
    seed.add_child(panel)
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    panel.set_content(column)
    column.add_child(make_text(tree, "TitleText", "Tech tree"))
    for i in range(LINE_COUNT):
        column.add_child(make_text(tree, "TechLine%d" % i, "-"))
    add_path_row(tree, column)
    add_tree_canvas(tree, column)
    add_law_row(tree, column)


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
