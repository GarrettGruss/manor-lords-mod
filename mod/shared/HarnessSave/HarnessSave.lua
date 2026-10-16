-- HarnessSave: the guarded harness save (spec 24). This is the ONLY place in the repo that calls a game save function.
-- The Python side (harness/runlib/harness_save.py) backs up the save folder, chooses a free slot name and checks the result.
-- This side refuses anything that does not look like a slot name from that guard, and refuses a slot that exists.
--
-- Game facts (docs/harness/24-mod-save-state/implementation-notes/save-hooks.md):
--   PawnCPP:requestSaveFile(SlotName, saveName) writes <SlotName>.sav into the REAL save folder. It overwrites without asking.
--   IoHandler:DoesSaveGameExist(SlotName) reads the real folder.
-- Rules: no eval. Call only on the game thread. Never call any other save function (autosave, slot save, menu save).

local M = {}

M.SLOT_PATTERN = "^saveGame_%d+$"
M.MAX_SLOT_CHARS = 20
M.NAME_PATTERN = "^[%w _%-]+$"
M.MAX_NAME_CHARS = 60
M.IO_HANDLER = "/Script/ManorLords.Default__IoHandler"

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function fail(message) return { ok = false, error = message } end

-- Return nil when the request is fine, else the reason.
function M.check_request(request)
    local slot, name = request.save_slot, request.save_name
    if type(slot) ~= "string" or #slot > M.MAX_SLOT_CHARS or not slot:match(M.SLOT_PATTERN) then
        return "slot must look like saveGame_<number>"
    end
    if type(name) ~= "string" or #name > M.MAX_NAME_CHARS or not name:match(M.NAME_PATTERN) then
        return "name must be letters, digits, space, '-' and '_' only, up to " .. M.MAX_NAME_CHARS .. " characters"
    end
    return nil
end

-- True or false. A check that cannot run counts as "exists", so the save is refused (fail closed).
local function slotExists(slot)
    local okFind, handler = pcall(StaticFindObject, M.IO_HANDLER)
    if not okFind or not isValid(handler) then return true, "IoHandler not found" end
    local okCall, exists = pcall(function() return handler:DoesSaveGameExist(slot) end)
    if not okCall then return true, "DoesSaveGameExist failed: " .. tostring(exists) end
    return exists == true, nil
end

local function findPlayer()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local ok, player = pcall(function() return engine.playerRef end)
    if ok and isValid(player) then return player end
    return nil
end

function M.save_game(request)
    local problem = M.check_request(request)
    if problem then return fail(problem) end
    local exists, why = slotExists(request.save_slot)
    if exists then return fail("refused: slot " .. request.save_slot .. " exists or could not be checked" .. (why and (" (" .. why .. ")") or "")) end
    local player = findPlayer()
    if not player then return fail("the player pawn is not loaded") end
    local ok, saved = pcall(function() return player:requestSaveFile(request.save_slot, request.save_name) end)
    if not ok then return fail("requestSaveFile failed: " .. tostring(saved)) end
    if saved == false then return fail("requestSaveFile returned false") end
    return { ok = true, slot = request.save_slot, name = request.save_name }
end

return M
