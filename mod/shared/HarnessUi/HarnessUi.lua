-- HarnessUi: show a text banner in the game and read the text back (spec 10, spike S9, criterion T4).
-- Why: a raid countdown needs a text with a number on screen. PawnCPP:playEventMessage(msgType Name, primaryText, secondaryText)
-- creates the banner widget `genericAchievement_EventMessage_C` (the "Raid in 2 days" style banner at the top of the screen).
-- The type must be an FName: a plain string crashes the game (spec 07 catalog). "Default" works.
-- The widget keeps the text in `Text` and `textSecondary`, and in the text blocks `main_txt` and `bottomTxt`. The module reads them back.
--
-- Rules: call only on the game thread. No save function. The text is checked before it is used: letters, digits, space and , . ! : -

local M = {}

M.WIDGET_CLASS = "genericAchievement_EventMessage_C"
M.MESSAGE_TYPE = "Default"
M.MAX_TEXT_CHARS = 60
M.MAX_SUBTEXT_CHARS = 80
M.MAX_LISTED = 8

local lastWidget = nil

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

-- Why a strict pattern: the text goes into the game as a string and into a JSON answer.
local function checkText(label, value, maxChars, required)
    if value == nil or value == "" then
        if required then return nil, label .. " is required" end
        return ""
    end
    if #value > maxChars then return nil, label .. " is longer than " .. maxChars .. " characters" end
    if value:find("[^%w ,%.!:%-]") then return nil, label .. " may use only letters, digits, space and , . ! : -" end
    return value
end

local function liveWidgets()
    local found = {}
    for _, widget in ipairs(FindAllOf(M.WIDGET_CLASS) or {}) do
        if isValid(widget) and not widget:GetFullName():find("Default__", 1, true) then found[#found + 1] = widget end
    end
    return found
end

local function describe(widget)
    return {
        text = textOf(read(function() return widget.Text end)),
        subtext = textOf(read(function() return widget.textSecondary end)),
        main_text = textOf(read(function() return widget.main_txt:GetText() end)),
        bottom_text = textOf(read(function() return widget.bottomTxt:GetText() end)),
        finished = read(function() return widget.animFinished end),
    }
end

local function nameSet(widgets)
    local set = {}
    for _, widget in ipairs(widgets) do set[widget:GetFullName()] = true end
    return set
end

local function newestOf(after, before)
    for _, widget in ipairs(after) do
        if not before[widget:GetFullName()] then return widget end
    end
    return nil
end

local function player()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local pawn = isValid(engine) and read(function() return engine.playerRef end)
    if not isValid(pawn) then return nil, "the player pawn is not loaded" end
    return pawn
end

-- Show a banner and return what the widget says. `shown` is false when no new widget appeared.
function M.show_message(request)
    local text, problem = checkText("text", request.text, M.MAX_TEXT_CHARS, true)
    if not text then return { ok = false, error = problem } end
    local subtext, problem2 = checkText("subtext", request.subtext, M.MAX_SUBTEXT_CHARS, false)
    if not subtext then return { ok = false, error = problem2 } end
    local pawn, problem3 = player()
    if not pawn then return { ok = false, error = problem3 } end
    local before = nameSet(liveWidgets())
    pawn:playEventMessage(FName(M.MESSAGE_TYPE), text, subtext)
    local widget = newestOf(liveWidgets(), before)
    if not widget then return { ok = true, shown = false, wanted = text } end
    lastWidget = widget
    local answer = describe(widget)
    answer.ok, answer.shown, answer.wanted = true, true, text
    return answer
end

-- The banner that show_message made last. `alive` is false after the game removed it.
function M.read_message()
    if not isValid(lastWidget) then return { ok = true, alive = false } end
    local answer = describe(lastWidget)
    answer.ok, answer.alive = true, true
    return answer
end

-- Every banner that is still in memory (old ones stay for a while).
function M.list_messages()
    local widgets = liveWidgets()
    local rows = {}
    for index, widget in ipairs(widgets) do
        if index > M.MAX_LISTED then break end
        rows[#rows + 1] = describe(widget)
    end
    return { ok = true, count = #widgets, messages = rows }
end

return M
