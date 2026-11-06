"""Tests for the feature order_tooltip (change add-order-tooltip-rows) in plain Lua through lupa.

The row builder is pure. The widget code runs against a stub tooltip made of Lua tables.
"""

import unittest

import fakegame_path  # noqa: F401
from lupa import LuaRuntime
from test_fakegame_modstate import find_pack_mod

PACK = find_pack_mod()

STUB = r"""
local Block = {}
Block.__index = Block
function Block.new(text) return setmetatable({ text = text or "", vis = 0 }, Block) end
function Block:SetText(t) self.text = t.s end
function Block:GetText() local s = self.text; return { ToString = function() return s end } end
function Block:SetColorAndOpacity(c) self.color = c end
function Block:SetVisibility(v) self.vis = v end
function Block:GetVisibility() return self.vis end

local Box = {}
Box.__index = Box
function Box.new() return setmetatable({ kids = {} }, Box) end
function Box:GetChildrenCount() return #self.kids end
function Box:GetChildAt(i) return self.kids[i + 1] end
function Box:AddChildToVerticalBox(w) self.kids[#self.kids + 1] = w end

local function native_row(d, v)
    local arrow = { angle = 180 }
    function arrow:GetClass() return { GetFName = function() return { ToString = function() return "Image" end } end } end
    function arrow:SetRenderTransformAngle(a) self.angle = a end
    function arrow:SetColorAndOpacity(c) self.color = c end
    function arrow:SetVisibility(v) self.vis = v end
    local bar = Box.new()
    bar:AddChildToVerticalBox(arrow)
    local r = { DescriptionText = Block.new(d), ValueText = Block.new(v), vis = 0, arrow = arrow,
        WidgetTree = { RootWidget = { GetChildAt = function() return bar end } } }
    function r:SetVisibility(x) self.vis = x end
    function r:GetVisibility() return self.vis end
    function r:IsValid() return true end
    return r
end

function FText(s) return { s = s } end
function StaticFindObject(path) return { Create = function() return native_row("", "") end } end
function FindFirstOf() return {} end

function new_tip(fail_add)
    local tip = { recentFactors_VB = Box.new(), pastFactors_VB = Box.new(), current_sum_txt = Block.new("-10%"), none_txt = Block.new("none") }
    tip.recentFactors_VB:AddChildToVerticalBox(native_row("Unemployment", "-10%"))
    if fail_add then
        function StaticFindObject() return { Create = function() error("boom") end } end
    end
    return tip
end
"""


class OrderTooltipTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        self.lua.execute(f'package.path = "{(PACK / "Scripts").as_posix()}/?.lua;" .. package.path')
        self.lua.execute(STUB)
        self.rows = self.lua.execute('return (require("features.order_tooltip.rows"))')

    def build(self, terms: str):
        return self.lua.eval(f'(function() local v = require("features.order_tooltip.rows").build({terms}); '
                             'if v == nil then return "nil" end; local out = { v.header }; '
                             'for _, r in ipairs(v.rows) do out[#out + 1] = r.text .. "|" .. r.value .. "|" .. r.color end; '
                             'return table.concat(out, ";") end)()')

    def test_tick_rows_and_header(self):
        self.assertEqual(self.build("{ order = 77, manor_term = 10, homeless_term = 10 }"),
                         "77%;Manor|+10|green;Homeless families|-10|red")

    def test_no_homeless_row_without_homeless(self):
        self.assertEqual(self.build("{ order = 100, manor_term = 10, homeless_term = 0 }"), "100%;Manor|+10|green")

    def test_no_manor_row_without_a_built_manor(self):
        self.assertEqual(self.build("{ order = 50, manor_term = 0, homeless_term = 10 }"), "50%;Homeless families|-10|red")
        self.assertEqual(self.build("{ order = 50, manor_term = 0, homeless_term = 0 }"), "50%")

    def test_tech_bonus_is_in_the_manor_term(self):
        self.assertEqual(self.build("{ order = 60, manor_term = 15, homeless_term = 0 }"), "60%;Manor|+15|green")

    def test_leave_row(self):
        self.assertEqual(self.build("{ order = 50, manor_term = 10, homeless_term = 5, leave_gain = 25 }"),
                         "50%;Manor|+10|green;Homeless families|-5|red;Peasants revolted|+25|green")

    def test_leave_row_before_first_tick(self):
        self.assertEqual(self.build("{ order = 50, leave_gain = 25 }"), "50%;Peasants revolted|+25|green")

    def test_before_first_tick_only_the_header(self):
        self.assertEqual(self.build("{ order = 100 }"), "100%")

    def test_no_mod_order_leaves_the_tooltip_native(self):
        self.assertEqual(self.build("nil"), "nil")
        self.assertEqual(self.build("{ }"), "nil")

    def test_widget_adds_rows_hides_native_and_sets_header(self):
        result = self.lua.eval("""(function()
            local widget = require("features.order_tooltip.widget")
            local rows = require("features.order_tooltip.rows")
            local tip = new_tip()
            local view = rows.build({ order = 77, manor_term = 10, homeless_term = 10 })
            local added = widget.apply(tip, view)
            local read = widget.read_rows(tip)
            return added .. "#" .. read.header .. "#" .. table.concat(read.rows, ";") .. "#" .. tip.recentFactors_VB.kids[1].vis
        end)()""")
        self.assertEqual(str(result), "2#77%#Manor | +10;Homeless families | -10#1")

    def test_positive_row_has_up_arrow_and_negative_row_down_arrow(self):
        result = self.lua.eval("""(function()
            local widget = require("features.order_tooltip.widget")
            local rows = require("features.order_tooltip.rows")
            local tip = new_tip()
            widget.apply(tip, rows.build({ order = 77, manor_term = 10, homeless_term = 10 }))
            local kids = tip.recentFactors_VB.kids
            return kids[2].arrow.angle .. "#" .. kids[3].arrow.angle
        end)()""")
        self.assertEqual(str(result), "0.0#180.0")

    def test_arrow_colour_follows_the_sign(self):
        result = self.lua.eval("""(function()
            local widget = require("features.order_tooltip.widget")
            local rows = require("features.order_tooltip.rows")
            local tip = new_tip()
            widget.apply(tip, rows.build({ order = 77, manor_term = 10, homeless_term = 10 }))
            local kids = tip.recentFactors_VB.kids
            local up, down = kids[2].arrow.color, kids[3].arrow.color
            return (up.G > up.R and up.G > up.B) and (down.R > down.G and down.R > down.B) and "ok" or "bad"
        end)()""")
        self.assertEqual(str(result), "ok")

    def notes(self, revolt: str) -> str:
        return self.lua.eval(f'(function() local v = require("features.order_tooltip.rows").build({{ order = 20, manor_term = 10, revolt = {revolt} }}); '
                             'local out = {}; for _, n in ipairs(v.notes) do out[#out + 1] = n.text .. "|" .. n.label .. "|" .. n.value .. "|" .. n.color end; '
                             'return table.concat(out, ";") end)()')

    def test_no_notes_without_a_timer(self):
        self.assertEqual(self.notes("nil"), "")

    def test_counter_shows_the_days(self):
        self.assertEqual(self.notes("{ days = 40 }"), "Peasants revolt in 40 days|Peasants revolt in|40 days|red")

    def test_counter_one_day_and_today(self):
        self.assertEqual(self.notes("{ days = 1 }"), "Peasants revolt in 1 day|Peasants revolt in|1 day|red")
        self.assertEqual(self.notes("{ days = 0 }"), "Peasants revolt today|Peasants revolt|today|red")

    def test_blocked_item_is_below_the_counter(self):
        self.assertEqual(self.notes('{ days = 12, blocked = "3 of 6 armed homes" }'),
                         "Peasants revolt in 12 days|Peasants revolt in|12 days|red;"
                         "Revolt blocked: 3 of 6 armed homes|Revolt blocked|3 of 6 armed homes|red")
        self.assertIn("Revolt blocked: no Outlaws pawn", self.notes('{ days = 12, blocked = "no Outlaws pawn" }'))

    def test_no_blocked_item_when_the_revolt_can_happen(self):
        self.assertNotIn("Revolt blocked", self.notes("{ days = 12 }"))

    def widget_notes(self, text_only: str) -> str:
        return str(self.lua.eval(f"""(function()
            local widget = require("features.order_tooltip.widget")
            local rows = require("features.order_tooltip.rows")
            local tip = new_tip()
            local view = rows.build({{ order = 20, manor_term = 10, revolt = {{ days = 40, blocked = "3 of 6 armed homes" }} }})
            local added = widget.apply(tip, view, {text_only})
            local kids = tip.recentFactors_VB.kids
            local counter, flag = kids[3], kids[4]
            return added .. "#" .. counter.DescriptionText.text .. "#" .. counter.ValueText.vis .. "#" .. counter.arrow.vis ..
                "#" .. flag.DescriptionText.text .. "#" .. flag.ValueText.text .. "#" .. flag.ValueText.vis
        end)()""")).replace("\n", "")

    def test_widget_draws_text_items_without_a_value(self):
        self.assertEqual(self.widget_notes("true"),
                         "3#Peasants revolt in 40 days#1#1#Revolt blocked: 3 of 6 armed homes##1")

    def test_widget_fallback_draws_label_and_value(self):
        self.assertEqual(self.widget_notes("false"),
                         "3#Peasants revolt in#0#1#Revolt blocked#3 of 6 armed homes#0")

    def test_failing_widget_call_raises_for_the_caller_to_log(self):
        ok = self.lua.eval("""(function()
            local widget = require("features.order_tooltip.widget")
            local rows = require("features.order_tooltip.rows")
            local tip = new_tip(true)
            local ok, err = pcall(widget.apply, tip, rows.build({ order = 77, manor_term = 10, homeless_term = 0 }))
            return tostring(ok) .. "#" .. tostring(err)
        end)()""")
        self.assertTrue(str(ok).startswith("false#"))
        self.assertIn("boom", str(ok))


if __name__ == "__main__":
    unittest.main()
