-- HarnessPolicies: read and enact the policies (edicts) of the player's region (spec 16, issue #55).
-- Why: the game has a policy system. PawnCPP:enactPolicy(Region, slotNo, policyID) signs a policy, Region:getMaxPolicies() is the
-- number of slots, Region:getAllAvailablePolicies() lists the ids that can be chosen, and Region:setPolicySigned(id, bool) sets the
-- signed state. The policy rows are in the DataTable DT_PolicyTypes (row index = policy id, EPolicyType). The Region calls need object
-- references, so they live here as named commands.
--
-- Rules: call only on the game thread. No save function. Every input is checked before it is used. policy_state only reads.
-- Struct arrays (Region.policies, summedApprovalFactors) are read element by element, without :get() (it crashes the game, spike S11).
-- The Policy field Icon is an object field and is never read.

local sack = require("HarnessSack")

local M = {}

M.MAX_POLICY_ID = 40
M.MAX_SLOTS = 20
M.MAX_FACTORS = 40

local FACTOR_NAMES = {
    [0] = "hunger", "starvation", "cold", "freezing", "death", "homelessness", "missingMarketFood", "missingMarketFirewood",
    "missingMarketCloth", "missingMarketLeather", "noWaterAccess", "missingChurch", "foodVarietyGood", "churchLevelGood",
    "clothSuppliesGood", "lowApproval", "drinking", "unemployment", "patrols", "administration", "no_administration", "hardship",
    "missingEntertainment", "unburied", "taxation", "NewFortune_BurgagePlotLv1Buff", "FromTheAshes_ApprovalBuff",
    "FromTheAshes_ApprovalAndInfluenceOnDeath", "ApprovalOfTradeRoutes", "ApprovalFromMilitiaEquipment", "MissingMarketCommodities",
    "MissingAmenities", "SatisfiedMarketCommodities", "SatisfiedAmenities",
}

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

local function textOf(value)
    if value == nil then return nil end
    if type(value) == "string" then return value end
    return read(function() return value:ToString() end)
end

local function count(array)
    if array == nil then return 0 end
    if type(array) == "table" then return #array end
    return read(function() return array:GetArrayNum() end) or 0
end

-- A number array: each element may need :get().
local function numbers(array)
    local out = {}
    for i = 1, count(array) do
        local element = array[i]
        if type(element) == "number" then
            out[#out + 1] = element
        else
            out[#out + 1] = read(function() return element:get() end)
        end
    end
    return out
end

local function playerPawn()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local pawn = isValid(engine) and read(function() return engine.playerRef end)
    if not isValid(pawn) then return nil, "the player pawn is not loaded" end
    return pawn
end

local function context()
    local pawn, problem = playerPawn()
    if not pawn then return nil, nil, problem end
    local region, problem2 = sack.playerRegion()
    if not region then return nil, nil, problem2 end
    return pawn, region
end

local function policyRows(region)
    local rows = {}
    local array = read(function() return region.policies end)
    for i = 1, math.min(count(array), M.MAX_SLOTS) do
        local element = array[i]
        rows[#rows + 1] = {
            slot = i - 1,
            id = read(function() return element.ID end),
            tier = read(function() return element.tier end),
            name = textOf(read(function() return element.Name end)),
            time_left = read(function() return element.timeLeft end),
        }
    end
    return rows
end

local function approvalFactors(region)
    local rows = {}
    local array = read(function() return region.summedApprovalFactors end)
    for i = 1, math.min(count(array), M.MAX_FACTORS) do
        local element = array[i]
        local kind = read(function() return element.Type end)
        rows[#rows + 1] = {
            type = kind,
            name = FACTOR_NAMES[kind],
            day = read(function() return element.day end),
            expiration_day = read(function() return element.expirationDay end),
            count = read(function() return element.count end),
            past = read(function() return element.past end),
            effect_by_population = read(function() return element.effectByPopulation end),
        }
    end
    return rows
end

local function snapshot(pawn, region)
    local available = read(function() return region:getAllAvailablePolicies() end)
    local available_ids = numbers(available and (read(function() return available:get() end) or available))
    return {
        region = read(function() return region:GetFName():ToString() end),
        max_policies = read(function() return region:getMaxPolicies() end),
        policies = policyRows(region),
        signed = numbers(read(function() return region.policiesSigned end)),
        available = available_ids,
        pawn_available = numbers(read(function() return pawn.availablePolicies end)),
        approval = read(function() return region.Approval end),
        approval_factors = approvalFactors(region),
        taxes_approval_loss = read(function() return region:getPredictedApprovalLossFromTaxes() end),
        dev_points_spent = read(function() return region:getNumDevPointsSpent() end),
        settlement_level = read(function() return region.settlementLevel end),
        regional_wealth = read(function() return region.regionalWealth end),
        silver = read(function() return pawn.silver end),
        influence = read(function() return pawn.influence end),
        population = read(function() return region:getNumTotalPopulation() end),
    }
end

-- Read only: policies, slots, approval and its factors, and the resources a policy might cost.
function M.policy_state()
    local pawn, region, problem = context()
    if not pawn then return { ok = false, error = problem } end
    local answer = snapshot(pawn, region)
    answer.ok = true
    return answer
end

local function checkPolicyId(value)
    if type(value) ~= "number" or value ~= math.floor(value) or value < 1 or value > M.MAX_POLICY_ID then
        return nil, "policy must be a whole number from 1 to " .. M.MAX_POLICY_ID
    end
    return value
end

local function contains(list, value)
    for _, item in ipairs(list) do if item == value then return true end end
    return false
end

-- Enact one policy with the game's own call. Refused when the policy is not in the available list, or the slot is outside
-- the slot count. The answer holds the state before and after, and the game's return value.
function M.policy_enact(request)
    local policy, problem = checkPolicyId(request.policy)
    if not policy then return { ok = false, error = problem } end
    local pawn, region, problem2 = context()
    if not pawn then return { ok = false, error = problem2 } end
    local before = snapshot(pawn, region)
    local slot = request.slot
    if type(slot) ~= "number" or slot ~= math.floor(slot) or slot < 0 or slot >= (before.max_policies or 0) then
        return { ok = false, error = "slot must be a whole number from 0 to " .. tostring((before.max_policies or 0) - 1), before = before }
    end
    if not contains(before.available, policy) then
        return { ok = false, error = "policy " .. policy .. " is not in the available list", before = before }
    end
    local returned = pawn:enactPolicy(region, slot, policy)
    local value = read(function() return returned:get() end)
    if value == nil then value = returned end
    return { ok = true, returned = value, before = before, after = snapshot(pawn, region) }
end

-- Unsafe spike command (issue #60): call enactPolicy with many slots and ids and no pre-check, to find when it returns true.
-- It stops at the first true. Test games only (HARNESS_ALLOW_UNSAFE=1).
M.UNSAFE_ENV = "HARNESS_ALLOW_UNSAFE"
M.SWEEP_SLOTS = { -1, 0, 1, 2, 3 }
M.SWEEP_MAX_ID = 18

function M.policy_enact_sweep()
    if (os.getenv and os.getenv(M.UNSAFE_ENV)) ~= "1" then
        return { ok = false, error = "policy_enact_sweep is an unsafe test command: start the game with " .. M.UNSAFE_ENV .. "=1 (test games only)" }
    end
    local pawn, region, problem = context()
    if not pawn then return { ok = false, error = problem } end
    local results, first_true = {}, nil
    for id = 0, M.SWEEP_MAX_ID do
        for _, slot in ipairs(M.SWEEP_SLOTS) do
            local returned = pawn:enactPolicy(region, slot, id)
            local value = read(function() return returned:get() end)
            if value == nil then value = returned end
            results[#results + 1] = { id = id, slot = slot, returned = value }
            if value == true then first_true = { id = id, slot = slot }; break end
        end
        if first_true then break end
    end
    return { ok = true, calls = #results, first_true = first_true, results = results, after = snapshot(pawn, region) }
end

-- Set the signed state of a policy with Region:setPolicySigned (the call the policy widget uses).
function M.policy_sign(request)
    local policy, problem = checkPolicyId(request.policy)
    if not policy then return { ok = false, error = problem } end
    if type(request.signed) ~= "boolean" then return { ok = false, error = "signed must be true or false" } end
    local pawn, region, problem2 = context()
    if not pawn then return { ok = false, error = problem2 } end
    local before = snapshot(pawn, region)
    region:setPolicySigned(policy, request.signed)
    return { ok = true, before = before, after = snapshot(pawn, region) }
end

-- ---- Menu probe (spec 16, question Q5b): a Lua-made screen that reuses the game's own policy widget ----
-- The game builds a policy button with the Blueprint class policyWidget_C (it has a Button, an image and a tooltip, and its own click
-- handler). The module makes one new instance with WidgetBlueprintLibrary:Create, gives it a policy id and the region, and puts it on
-- the screen. It does not edit game files. A click needs the real mouse. The state of the button is polled (no delegate binding from Lua).

M.WIDGET_CLASS_PATH = "/Game/UI/Development_Tree/policyWidget.policyWidget_C"
M.MENU_Z_ORDER = 500

local probe = nil

local function describeProbe()
    if not isValid(probe) then return { alive = false } end
    local button = read(function() return probe.Button_22 end)
    return {
        alive = true,
        name = read(function() return probe:GetFullName() end),
        policy_id = read(function() return probe.policyID end),
        tier = read(function() return probe.policyTier end),
        wip = read(function() return probe.wip end),
        in_viewport = read(function() return probe:IsInViewport() end),
        visibility = read(function() return probe:GetVisibility() end),
        button_valid = isValid(button),
        button_pressed = isValid(button) and read(function() return button:IsPressed() end),
        button_hovered = isValid(button) and read(function() return button:IsHovered() end),
    }
end

function M.menu_probe_show(request)
    local policy, problem = checkPolicyId(request.policy)
    if not policy then return { ok = false, error = problem } end
    local pawn, region, problem2 = context()
    if not pawn then return { ok = false, error = problem2 } end
    if isValid(probe) then return { ok = false, error = "a probe widget is already on the screen; call menu_probe_hide first" } end
    local class = StaticFindObject(M.WIDGET_CLASS_PATH)
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local controller = FindFirstOf("PlayerController")
    if not (isValid(class) and isValid(library) and isValid(controller)) then
        return { ok = false, error = "widget class, library or player controller not found" }
    end
    local widget = library:Create(pawn, class, controller)
    if not isValid(widget) then return { ok = false, error = "WidgetBlueprintLibrary:Create returned no widget" } end
    widget.policyID = policy
    widget.policyTier = 1
    widget.Region = region
    widget:AddToViewport(M.MENU_Z_ORDER)
    widget:SetPositionInViewport({ X = request.x or 300, Y = request.y or 300 }, false)
    probe = widget
    local answer = describeProbe()
    answer.ok = true
    return answer
end

function M.menu_probe_read()
    local answer = describeProbe()
    answer.ok = true
    return answer
end

function M.menu_probe_hide()
    if isValid(probe) then probe:RemoveFromParent() end
    probe = nil
    return { ok = true, alive = false }
end

return M
