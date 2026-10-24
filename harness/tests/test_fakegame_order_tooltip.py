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
    local r = { DescriptionText = Block.new(d), ValueText = Block.new(v), vis = 0 }
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

    def test_tech_bonus_is_in_the_manor_term(self):
        self.assertEqual(self.build("{ order = 60, manor_term = 15, homeless_term = 0 }"), "60%;Manor|+15|green")

    def test_leave_row(self):
        self.assertEqual(self.build("{ order = 50, manor_term = 10, homeless_term = 5, leave_gain = 25 }"),
                         "50%;Manor|+10|green;Homeless families|-5|red;Left for banditry|+25|green")

    def test_leave_row_before_first_tick(self):
        self.assertEqual(self.build("{ order = 50, leave_gain = 25 }"), "50%;Left for banditry|+25|green")

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
