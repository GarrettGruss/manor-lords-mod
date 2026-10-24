-- Feature order_tooltip: the game's Public Order tooltip shows the mod order terms as rows and the mod order in its header.
-- A pre-hook on BigTooltip_ApprovalAndPublicOrder_C:updateContents runs at each open. The game rebuilds the rows after the pre callback,
-- so the rows are added after a short delay (the post callback does not fire; spike #422).
-- If the hook cannot be set or a widget call fails, the tooltip stays native and the mod logs the problem once.
local core = require("ManorCore")
local rows = require("features.order_tooltip.rows")
local widget = require("features.order_tooltip.widget")
local bandits = require("features.bandits.init")
local config = require("config").order_tooltip

local TAG = "InvasionMod.order_tooltip"
local HOOK_PATH = "/Game/UI/Tooltips/BigTooltip_ApprovalAndPublicOrder.BigTooltip_ApprovalAndPublicOrder_C:updateContents"

local S = { hooked = false, generation = 0, opens = 0, applied = 0, last_error = nil, last_rows = 0, error_logged = false }

local function fail(message)
    S.last_error = message
    if not S.error_logged then
        S.error_logged = true
        core.log.error(TAG, "order tooltip: " .. message)
    end
end

local function apply_now(tip, generation)
    if generation ~= S.generation then return end -- a newer open is on its way
    local view = rows.build(bandits.order_terms())
    if view == nil then return end
    local ok, result = pcall(widget.apply, tip, view)
    if ok then
        S.applied = S.applied + 1
        S.last_rows = result
    else
        fail(tostring(result))
    end
end

local function on_update_contents(self)
    S.opens = S.opens + 1
    S.generation = S.generation + 1
    local generation = S.generation
    local ok, tip = pcall(function() return self:get() end)
    if not ok or tip == nil then return fail("the tooltip object was not given by the hook") end
    ExecuteWithDelay(config.delay_ms, function()
        ExecuteInGameThread(function() apply_now(tip, generation) end)
    end)
end

-- The widget class loads late, so the hook is set at the first poll where RegisterHook works.
local function try_hook()
    if S.hooked then return end
    local ok, problem = pcall(RegisterHook, HOOK_PATH, on_update_contents)
    if ok then
        S.hooked = true
        core.log.info(TAG, "order tooltip hook set")
    else
        S.hook_error = tostring(problem)
    end
end

require("scheduler").every(TAG, config.poll_ms, try_hook)

local has_commands, commands = pcall(require, "HarnessCommands")
if has_commands then
    commands.register("InvasionMod.order_tooltip_state", function()
        local result = { hooked = S.hooked, opens = S.opens, applied = S.applied, last_rows = S.last_rows,
            last_error = S.last_error, hook_error = S.hook_error }
        local tip = FindFirstOf("BigTooltip_ApprovalAndPublicOrder_C")
        if tip ~= nil and tip:IsValid() then
            local ok, read = pcall(widget.read_rows, tip)
            if ok then result.header, result.rows = read.header, read.rows else result.read_error = tostring(read) end
        end
        return result
    end, {})
end

core.log.info(TAG, "feature order_tooltip loaded")
return { state = S }
