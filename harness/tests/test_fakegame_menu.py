"""Tests for the base menu (Scripts/core/menu.lua) of the pack mod in the fake game.

They run the real Lua files with widget stand-ins (plain Lua tables with the calls the base menu makes). They prove the logic:
bottom bar buttons, click hooks, one menu at a time, the backdrop and its click, and the reload of the HUD. They do not prove how the
real game behaves (the test scenario `menu-base` does).
"""

import unittest

import fakegame_path  # noqa: F401
from test_fakegame_invasion import InvasionTestCase

BAR_CLASS = "/Game/UI/HUD/mainTabButton.mainTabButton_C"
LUA_STUBS = """
T = { created = {}, closed = {}, opened = {}, counter = 0, game_buttons = 6 }
local function new(name)
    local w = { name = name, children = {}, valid = true }
    function w:IsValid() return self.valid end
    function w:GetFName() return { ToString = function() return name end } end
    function w:GetFullName() return "Widget /Game/" .. name end
    function w:AddToViewport(z) self.z = z; self.viewport = true; if self == T.last_bar then T.close_widget = self end end
    function w:RemoveFromParent() self.viewport = false end
    function w:SetVisibility(v) self.vis = v end
    function w:GetVisibility() return self.vis end
    function w:SetPositionInViewport(p) self.pos = p end
    function w:SetAnchorsInViewport(a) self.anchors = a end
    function w:SetAlignmentInViewport() end
    function w:SetBackgroundColor(c) self.bg = c end
    function w:SetText(t) self.text = t end
    function w:SetColorAndOpacity() end
    function w:AddChildToHorizontalBox(c) table.insert(self.children, c) end
    function w:AddChildToOverlay(c) table.insert(self.children, c) end
    function w:GetChildrenCount() return #self.children end
    function w:GetChildAt(i) return self.children[i + 1] end
    w.OnClicked = { Add = function(_, fn) w.click = fn end }
    return w
end
T.new = new

function T.make_hud()
    local hud = new("MainUICPP_C_" .. (T.counter + 1))
    T.counter = T.counter + 1
    hud.main_tabs_HB = new("main_tabs_HB")
    for i = 1, T.game_buttons do table.insert(hud.main_tabs_HB.children, new("gameButton" .. i)) end
    T.hud = hud
    return hud
end

local library = {}
function library:IsValid() return true end
function library:Create(_, class)
    T.counter = T.counter + 1
    local w = new(class.tag .. "_" .. T.counter)
    if class.tag == "bar" then
        T.last_bar = w
        w.WidgetTree = { RootWidget = new("Overlay") }
        w.WidgetTree.IsValid = function() return true end
        w.WidgetTree.RootWidget.WidgetTree = nil
        w.children = { w.WidgetTree.RootWidget }
    end
    if class.tag == "content" then T.created[#T.created + 1] = w end
    if class.tag == "user" then T.blocker_user = w end
    return w
end
local classes = {
    ["/Script/UMG.Default__WidgetBlueprintLibrary"] = library,
    ["/Script/UMG.UserWidget"] = { tag = "user", IsValid = function() return true end },
    ["/Script/UMG.WidgetTree"] = { tag = "tree", IsValid = function() return true end },
    ["/Script/UMG.Button"] = { tag = "button", IsValid = function() return true end },
    ["/Script/UMG.TextBlock"] = { tag = "text", IsValid = function() return true end },
    ["BAR_CLASS"] = { tag = "bar", IsValid = function() return true end },
    ["/Game/Test/WBP_A.WBP_A_C"] = { tag = "content", IsValid = function() return true end },
    ["/Game/Test/WBP_B.WBP_B_C"] = { tag = "content", IsValid = function() return true end },
}
-- the fake kit has no FName and no FText
FName = function(text) return setmetatable({ text = text }, { __index = { ToString = function(self) return self.text end } }) end
FText = function(text) return text end
local real_static, real_first, real_all = StaticFindObject, FindFirstOf, FindAllOf
T.borders = {}
FindAllOf = function(class)
    if class == "Border" then return T.borders end
    return real_all(class)
end
StaticFindObject = function(path) return classes[path] or real_static(path) end
FindFirstOf = function(class)
    if class == "PlayerController" then return T.new("controller") end
    if class == "MainUICPP_C" then return T.hud end
    return real_first(class)
end
StaticConstructObject = function(class, _, name)
    local w = new(name:ToString())
    w.tag = class.tag
    if class.tag == "button" then T.blocker_button = w end
    return w
end

local menu = require("core.menu")
T.menu = menu
for _, id in ipairs({ "a", "b" }) do
    menu.register({
        id = id, label = "Test " .. id, class_path = "/Game/Test/WBP_" .. id:upper() .. ".WBP_" .. id:upper() .. "_C",
        package_path = "/Game/Test", asset_name = "WBP_" .. id:upper(), position = { X = 10, Y = 20 },
        on_open = function(widget) T.opened[#T.opened + 1] = id; T["widget_" .. id] = widget; return true end,
        on_close = function() T.closed[#T.closed + 1] = id end,
    })
end
menu.register({ id = "bad", label = "Bad", class_path = "/Game/Test/WBP_A.WBP_A_C", package_path = "/Game/Test", asset_name = "WBP_A",
    on_open = function() return nil, "no buttons" end, on_close = function() end })
"""


class MenuTests(InvasionTestCase):
    def setUp(self):
        super().setUp()
        self.game.exec(LUA_STUBS.replace("BAR_CLASS", BAR_CLASS))

    def lua(self, code):
        return self.game.lua.eval(f"(function() {code} end)")()

    def state_value(self, expression):
        return self.lua(f"return {expression}")

    def make_hud_and_wait(self):
        self.lua("T.make_hud()")
        self.game.advance(2)

    def bar_children(self):
        return self.state_value("#T.hud.main_tabs_HB.children")

    def click_bar_button(self, index):
        """The hook of the game's button class fires for the clone at index (1 = first mod button)."""
        self.lua(f"T.clicked = T.hud.main_tabs_HB.children[T.game_buttons + {index}]")
        self.game.fire_hook(BAR_CLASS + ":HandleClicked", self.lua("return T.clicked"))
        self.game.advance(1)

    def test_the_real_menus_are_registered_in_a_fixed_order(self):
        registered = self.lua("local r = T.menu.state().registered; return table.concat({ r[1], r[2], r[3], r[4] }, ',')")
        self.assertEqual(registered, "raid,tech,tribute,a")

    def test_the_buttons_are_added_after_the_games_buttons_with_a_label(self):
        self.make_hud_and_wait()
        self.assertEqual(self.bar_children(), 6 + 6)
        labels = self.lua("""local out = {}
            for i = 7, 12 do local b = T.hud.main_tabs_HB.children[i]; out[#out + 1] = tostring(b.children[1].children[1].text) end
            return table.concat(out, ',')""")
        self.assertEqual(labels, "Raid,Tech,Liege,Test a,Test b,Bad")
        self.assertIsNone(self.state_value("T.menu.state().bar_error"))

    def test_the_buttons_are_added_once(self):
        self.make_hud_and_wait()
        self.game.advance(5)
        self.assertEqual(self.bar_children(), 12)

    def test_a_click_on_a_mod_button_opens_its_menu_in_one_click(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.assertEqual(self.state_value("T.menu.state().open_id"), "a")
        self.assertEqual(self.state_value("T.menu.state().press_count"), 1)

    def test_a_click_on_a_game_button_is_ignored(self):
        self.make_hud_and_wait()
        self.game.fire_hook(BAR_CLASS + ":HandleClicked", self.lua("return T.hud.main_tabs_HB.children[1]"))
        self.game.advance(1)
        self.assertEqual(self.state_value("T.menu.state().press_count"), 0)
        self.assertFalse(self.state_value("T.menu.state().open"))

    def test_a_second_click_on_the_button_closes_the_menu(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.click_bar_button(4)
        self.assertFalse(self.state_value("T.menu.state().open"))
        self.assertEqual(self.lua("return table.concat(T.closed, ',')"), "a")

    def test_the_hover_hook_records_the_hovered_menu(self):
        self.make_hud_and_wait()
        self.game.fire_hook(BAR_CLASS + ":HandleHovered", self.lua("return T.hud.main_tabs_HB.children[T.game_buttons + 5]"))
        self.assertEqual(self.state_value("T.menu.state().hover_id"), "b")

    def test_an_open_menu_is_fullscreen_with_a_blocking_backdrop_under_the_content(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.assertTrue(self.state_value("T.menu.state().blocker"))
        self.assertEqual(self.state_value("T.menu.state().blocker_visibility"), 0)  # Visible
        self.assertEqual(self.state_value("T.widget_a.z"), 500)
        self.assertEqual(self.state_value("T.widget_a.pos.X"), 10)
        self.assertEqual(self.state_value("T.blocker_user.z"), 450)  # below the content, above the HUD
        self.assertEqual(self.state_value("T.blocker_user.anchors.Maximum.X"), 1)  # the full viewport
        self.assertEqual(self.state_value("T.blocker_button.tag"), "button")  # a Button blocks a click, a Border does not
        self.assertEqual(self.state_value("T.blocker_button.bg.A > 0"), True)

    def test_the_backdrop_button_has_no_click_callback(self):
        # OnClicked:Add on a Button made at run time crashed the real game (notes/menu-findings.md).
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.assertIsNone(self.state_value("T.blocker_button.click"))

    def test_the_close_button_closes_the_menu_and_leaves_no_widget(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.assertTrue(self.state_value("T.menu.state().close_button"))
        self.assertEqual(self.state_value("T.close_widget.z"), 510)
        self.game.fire_hook(BAR_CLASS + ":HandleClicked", self.lua("return T.close_widget"))
        self.game.advance(1)
        self.assertFalse(self.state_value("T.menu.state().open"))
        self.assertEqual(self.state_value("T.menu.state().close_presses"), 1)
        self.assertFalse(self.state_value("T.close_widget.viewport"))
        self.assertFalse(self.state_value("T.blocker_user.viewport"))
        self.assertFalse(self.state_value("T.widget_a.viewport"))

    def test_borders_of_the_content_let_clicks_reach_the_backdrop_and_other_borders_stay(self):
        self.make_hud_and_wait()
        self.lua("""T.ours = T.new('Border_ours')
            T.ours.GetFullName = function() return 'Border /Game/' .. T.widget_a.name .. '.Border_ours' end
            T.game = T.new('Border_game')
            T.game.GetFullName = function() return 'Border /Game/MainUICPP_C_1.Border_game' end
            T.borders = { T.ours, T.game }""")
        self.click_bar_button(4)
        self.assertEqual(self.state_value("T.ours.vis"), 4)
        self.assertIsNone(self.state_value("T.game.vis"))
        self.assertEqual(self.state_value("T.widget_a.vis"), 4)
        self.assertEqual(self.state_value("T.menu.state().pass_through"), 1)

    def test_opening_a_second_menu_closes_the_first(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.click_bar_button(5)
        self.assertEqual(self.state_value("T.menu.state().open_id"), "b")
        self.assertEqual(self.lua("return table.concat(T.closed, ',')"), "a")
        self.assertFalse(self.state_value("T.widget_a.viewport"))
        self.assertTrue(self.state_value("T.widget_b.viewport"))

    def test_a_menu_that_fails_to_open_leaves_no_widget_and_says_why(self):
        self.make_hud_and_wait()
        self.click_bar_button(6)
        self.assertFalse(self.state_value("T.menu.state().open"))
        self.assertFalse(self.state_value("T.menu.state().blocker"))
        self.assertIn("no buttons", self.state_value("T.menu.state().last_error"))

    def test_an_unknown_menu_is_refused(self):
        answer = self.lua("local r = T.menu.open('nope'); return tostring(r.ok) .. ':' .. r.error")
        self.assertEqual(answer, "false:unknown menu: nope")

    def test_a_duplicate_id_is_refused_with_a_clear_message(self):
        message = self.lua("""local ok, err = pcall(T.menu.register, { id = 'a', label = 'x', class_path = 'x', package_path = 'x',
            asset_name = 'x', on_open = function() end, on_close = function() end })
            return tostring(ok) .. ':' .. tostring(err)""")
        self.assertEqual(message, "false:menu.register: duplicate menu id a")

    def test_a_new_hud_widget_after_a_game_load_gets_the_buttons_again(self):
        self.make_hud_and_wait()
        self.assertEqual(self.bar_children(), 12)
        self.make_hud_and_wait()  # a load makes a new HUD with only the game's buttons
        self.assertEqual(self.bar_children(), 12)
        self.assertNotEqual(self.state_value("T.hud.main_tabs_HB.children[7].name"), "gameButton7")

    def test_a_missing_bar_panel_is_reported_and_does_not_raise(self):
        self.lua("local hud = T.make_hud(); hud.main_tabs_HB = nil; hud.children = {}")
        self.game.advance(3)
        self.assertIn("main_tabs_HB", self.state_value("T.menu.state().bar_error"))

    def test_the_key_shortcut_goes_through_the_base_menu(self):
        self.game.press("F8")
        self.game.advance(1)
        # The raid menu pak is not in the fake game, so the open fails, and the base menu keeps the reason.
        self.assertEqual(self.state_value("T.menu.state().last_error"), "AssetRegistryHelpers not found")

    def test_a_menu_widget_that_the_game_removed_is_closed(self):
        self.make_hud_and_wait()
        self.click_bar_button(4)
        self.lua("T.widget_a.valid = false")
        self.game.advance(1)
        self.assertFalse(self.state_value("T.menu.state().open"))
        self.assertEqual(self.lua("return table.concat(T.closed, ',')"), "a")


if __name__ == "__main__":
    unittest.main()
