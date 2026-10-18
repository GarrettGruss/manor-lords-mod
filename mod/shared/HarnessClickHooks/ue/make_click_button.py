# Runs inside UnrealEditor-Cmd (-ExecutePythonScript). Makes /Game/HarnessMod/WBP_ClickButton (spec 34).
# Why a copy of an engine widget: the Python API of UE 5.5 cannot create graph nodes. The engine widget
# /AudioWidgets/AudioButtonToggle already has a graph with an OnClicked event of its root button (Button01).
# At run time that event is a UFunction called through ProcessEvent, so a UE4SS hook sees it.
# The button text is the TextBlock ValueText. Lua sets it. The images have no texture, so no plugin asset is needed.
import unreal

SOURCE = "/AudioWidgets/AudioButtonToggle/AudioButtonToggle"
FULL = "/Game/HarnessMod/WBP_ClickButton"
BUTTON = "Button01"
TEXT_BORDER = "TextBorder"
TEXT = "ValueText"
IMAGES = ["LeftBoxTop", "LeftCurveTop", "LeftBoxBottom", "LeftCurveBottom",
          "RightBoxTop", "RightCurveTop", "RightBoxBottom", "RightCurveBottom"]


def log(msg):
    unreal.log("CLICKBTN: " + str(msg))


def need(tree, name):
    found = unreal.find_object(tree, name)
    if not found:
        raise RuntimeError("widget not found: " + name)
    return found


def clear_image(image):
    brush = image.get_editor_property("brush")
    brush.set_editor_property("resource_object", None)
    brush.set_editor_property("draw_as", unreal.SlateBrushDrawType.NO_DRAW_TYPE)
    image.set_editor_property("brush", brush)


def main():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        unreal.EditorAssetLibrary.delete_asset(FULL)
    bp = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, FULL)
    tree = unreal.find_object(bp, "WidgetTree")
    need(tree, BUTTON)
    for name in IMAGES:
        clear_image(need(tree, name))
    border = need(tree, TEXT_BORDER)
    border.set_editor_property("brush_color", unreal.LinearColor(0.20, 0.15, 0.08, 0.95))
    border.set_editor_property("padding", unreal.Margin(10, 4, 10, 4))
    label = need(tree, TEXT)
    label.set_editor_property("text", "-")
    # Python cannot make ValueText a variable. Lua walks from the variable Button01: content, child 1 (TextBorder), content.
    unreal.EditorAssetLibrary.save_asset(FULL)
    log("DONE")


main()
