# Runs inside UnrealEditor-Cmd (-ExecutePythonScript).
# Makes /Game/HarnessMod/WBP_ScenarioSettings from a stock engine widget (same method as make_raid_widget.py).
# The scenario settings menu (change add-scenario-settings-menu): a title, a background text, five rows (a label and up to four
# choice buttons) and two buttons. Lua puts a WBP_ClickButton into each Border (HarnessClickHooks) and fills the texts.
# Lua finds the widgets by name: SettingsTitle, BackgroundText, RowLabel0..4, Choice<row>_<choice> (row 0..4, choice 0..3),
# DefaultsButton, BeginButton.
# Look: parchment colours (a Border brush colour and dark text). The PNG images of the mockup are not in this pak yet.
import unreal

SOURCE = "/MoverExamples/Widgets/ControlsDisplay"
PATH = "/Game/HarnessMod"
NAME = "WBP_ScenarioSettings"
FULL = PATH + "/" + NAME
SEED_WIDGET = "StackBox_51"
ROW_COUNT = 5
CHOICE_COUNT = 4
LEFTOVER_FUNCTIONS = ["GatherInputInfo"]
PARCHMENT = unreal.LinearColor(0.62, 0.50, 0.30, 0.97)
INK = unreal.LinearColor(0.10, 0.06, 0.02, 1.0)
TEXT_WIDTH = 760.0


def log(msg):
    unreal.log("SSMENU: " + str(msg))


def copy_source():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    if not bp:
        raise RuntimeError("duplicate failed")
    return bp


def style_text(block, size):
    # Optional styling: a failure here must not stop the asset.
    try:
        block.set_editor_property("color_and_opacity", unreal.SlateColor(INK))
    except Exception as error:  # noqa: BLE001 - the editor API differs by version
        log("text colour failed: %s" % error)
    try:
        font = block.get_editor_property("font")
        font.set_editor_property("size", size)
        block.set_editor_property("font", font)
    except Exception as error:  # noqa: BLE001
        log("font size failed: %s" % error)


def make_text(tree, name, text, size):
    block = unreal.new_object(unreal.TextBlock, tree, name)
    block.set_editor_property("text", text)
    style_text(block, size)
    return block


def make_button_border(tree, name):
    # Lua puts a WBP_ClickButton into this border (spec 34). A Border paints white by default.
    border = unreal.new_object(unreal.Border, tree, name)
    border.set_editor_property("brush_color", unreal.LinearColor(0, 0, 0, 0))
    border.set_editor_property("padding", unreal.Margin(4, 2, 4, 2))
    return border


def add_menu(tree, seed):
    # Keep the seed widget: the copied graph refers to it by name.
    seed.clear_children()
    panel = unreal.new_object(unreal.Border, tree, "MenuPanel")
    panel.set_editor_property("brush_color", PARCHMENT)
    panel.set_editor_property("padding", unreal.Margin(32, 24, 32, 24))
    seed.add_child(panel)
    column = unreal.new_object(unreal.VerticalBox, tree, "MenuColumn")
    panel.set_content(column)
    column.add_child(make_text(tree, "SettingsTitle", "Scenario", 40))
    box = unreal.new_object(unreal.SizeBox, tree, "BackgroundBox")
    box.set_editor_property("width_override", TEXT_WIDTH)
    text = make_text(tree, "BackgroundText", "-", 20)
    try:
        text.set_editor_property("auto_wrap_text", True)
        text.set_editor_property("wrap_text_at", TEXT_WIDTH)
    except Exception as error:  # noqa: BLE001
        log("auto wrap failed: %s" % error)
    box.set_content(text)
    column.add_child(box)
    for row in range(ROW_COUNT):
        line = unreal.new_object(unreal.HorizontalBox, tree, "RowBox%d" % row)
        line.add_child(make_text(tree, "RowLabel%d" % row, "-", 24))
        for choice in range(CHOICE_COUNT):
            line.add_child(make_button_border(tree, "Choice%d_%d" % (row, choice)))
        column.add_child(line)
    buttons = unreal.new_object(unreal.HorizontalBox, tree, "ButtonRow")
    buttons.add_child(make_button_border(tree, "DefaultsButton"))
    buttons.add_child(make_button_border(tree, "BeginButton"))
    column.add_child(buttons)


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
    tree = unreal.find_object(bp, "WidgetTree")
    seed = unreal.find_object(tree, SEED_WIDGET)
    add_menu(tree, seed)
    drop_graphs(bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
