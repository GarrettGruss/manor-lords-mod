-- HarnessActions: runs a small, fixed list of commands inside the game for the Python action kit (spec 07).
-- Why: the bridge cannot pass object references, and some game functions need them (for example sendLetter).
--
--   client  ->  writes  <HARNESS_RUN_DIR>/commands/<id>.json         (write .tmp, then rename)
--   this mod -> runs it on the game thread, writes <id>.result.json  (write .tmp, then rename)
--
-- The ids are the numbers 0001, 0002, ... in order. UE4SS Lua cannot list a folder, so the mod
-- waits for the next number. The client must use the numbers in order.
-- Request shapes (a fixed small JSON, read with patterns, never run as code):
--   {"id":"0001","command":"ping"}
--   {"id":"0002","command":"send_letter","sender":1,"paragraphs":["name_one","name_two"]}
--   {"id":"0003","command":"autosave_status"}      read the autosave timer (read only)
--   {"id":"0004","command":"disable_autosave"}     restart the autosave timer with a one year period
--   {"id":"0005","command":"datatable_info"}       row count and names of the item table (read only)
--   {"id":"0006","command":"datatable_read","row":"name","field":"Value"}              one number field of one row
--   {"id":"0007","command":"datatable_write","row":"name","field":"Value","value":5}  change one number field
--      The three datatable commands take "table":"items" (default) or "table":"units" (DT_UnitTemplates, spec 10 spike S7).
--   {"command":"datatable_rows","table":"units"}               every row with every allowed number field (read only)
--   {"command":"popup_state"}                                  read the pop-up windows of the game (read only)
--   {"command":"close_popups"}                                 press Accept on every pop-up that is open ("Hunger!" and similar)
--   Raid and unit commands (spec 10, see mod/shared/HarnessRaids):
--   {"command":"raid_state"}                                   read the raid timer, the setup and the raid id lists
--   {"command":"units_census","sample":10}                     counts of units by side, role, state, region
--   {"command":"spawn_raiders","squads":2,"x":0,"y":0,"z":0}  RTSMultiEngineCPP:spawnRaiders (x, y, z optional)
--   {"command":"spawn_elite_raiders"}  {"command":"spawn_bandit_camp"}
--   {"command":"kill_units","side":"bandit","count":5}         SMUnit:just_die on live units of one side
--      kill_units also takes "with_loot":1 (only units that carry loot) and "actors":1 (report new actor classes)
--   {"command":"set_unit_loot","side":"bandit","count":3,"amount":5}   write ItemsLooted
--   Sack commands (spec 10, spike S6, see mod/shared/HarnessSack):
--   {"command":"sack_census"}                                  buildings by state, stock, stores, families and people of the player village
--   {"command":"sack_buildings","percent":50,"method":"collapse"}   burn ("fire") or collapse standing buildings ("count" instead of "percent" works too)
--   {"command":"sack_goods","percent":50}                      remove a share of every good; or "good":15,"amount":5,"store":<building id>
--   {"command":"sack_people","percent":40}                     kill every member of a share of the families ("count" works too)
--   {"command":"sack_village","buildings_pct":50,"stock_pct":50,"people_pct":40,"method":"collapse"}   all three
--   Loot stand-in (spec 10, spike R3, see mod/shared/HarnessLoot): the base game has no ground loot, so piles are a ledger
--   {"command":"drop_loot","side":"bandit","count":3,"good":17}   kill looters; a pile (place, amount, good) is recorded for each
--   {"command":"loot_piles"}                                    the piles
--   {"command":"recover_loot","pile":1}                         the goods of the pile go into the stock; the pile is gone
--   Unit and mercenary commands (spec 10, spikes S7, P5, C1, C2, see mod/shared/HarnessBattle):
--   {"command":"spawn_units","side":"player","template":"spearMilitia","count":1,"dx":0,"dy":0}   spawnArmy with a chosen template; dx, dy from the player pawn
--   {"command":"battle_state","detail":1}                      living units, experience and casualties of the squads that this mod spawned or hired
--   {"command":"clear_battle","side":"bandit"}                 kill the units of those squads (of one side if "side" is given) and forget them
--   {"command":"set_squad_experience","squad":8,"value":20}    write combatExperience on the living units of one of those squads
--   {"command":"mercenary_offers"}                             the companies that can be hired (read only)
--   {"command":"hire_mercenaries","company":"greencaps"}       hireMercs for one offered company; refused when the silver is below the cost
--   UI banner (spec 10, spike S9, see mod/shared/HarnessUi):
--   {"command":"show_message","text":"Raid in 3 days","subtext":"Prepare"}   playEventMessage; answers with the text that the widget holds
--   {"command":"read_message"}  the text of the banner that show_message made last    {"command":"list_messages"}  every banner in memory (read only)
--   Build commands (spec 10, spike R8, see mod/shared/HarnessBuild):
--   {"command":"building_sites","type":121}                the buildings of the village (one type if given): built, rubble, goods a site needs
--   {"command":"ruin_building","type":121,"method":"fire"}   burn or collapse the first built building of that type (it becomes Rubble)
--   {"command":"demolish_ruins"}                            demolish every ruin of the village
--   {"command":"set_site_cost","type":121,"good":17,"amount":2}   lower the amount of a good that a construction site needs (never raise)
--   Manor commands (spec 12, criterion M1, see mod/shared/HarnessManor):
--   {"command":"manor_state"}                               the manor modules of the village: built, goods, capacity, region manor
--   {"command":"finish_manor_site","type":57}               harness shortcut: finish a Keep site at once and register it as the region manor
--   {"command":"manor_put","good":27,"amount":20}           add goods to a built manor module (refused above the capacity of 200 units)
--   {"command":"manor_take","good":27,"amount":5}           remove goods from a manor module (refused when it holds less)
--   {"command":"manor_worker_slot","job":45,"slots":3}       give the manor module the worker slots of a Storehouse (job 45) or a Granary (job 44)
--   {"command":"manor_assign_worker"}                        assign one family without a workplace (or "family":N) to the manor module
--   {"command":"manor_unassign_workers"}                     take every family off the manor module
--   {"command":"manor_worker_state"}                         slots, job, assigned families and goods of the manor modules (read only)
--   AI lord commands (spec 10, spike S11, see mod/shared/HarnessLords). A lord is 1.. in FindAllOf("PawnCPP_AI") order; target 0 is the player:
--   {"command":"lords_state","log":12}                      every lord: traits, influence, enemies, squads with position and orders; challenges; AI logs
--   {"command":"lord_declare_war","lord":1,"target":0}      declareWar     {"command":"lord_declare_peace","lord":1,"target":0}   declarePeace
--   {"command":"lord_set_influence","lord":1,"value":500}   write the influence of the lord
--   {"command":"lord_challenge","lord":1,"target":0}        initChallenge over the target's current region
--   {"command":"lord_claim","lord":1,"target":0}            layClaim on the target's current region
--   {"command":"lord_spawn_army","lord":1,"template":"spearMilitia","count":2,"dx":0,"dy":0}   spawnArmy with the lord as owner
--   {"command":"spawn_ai_lord","name":"Norse Warlord","build":1}   spawnNewAILord ("build":1 = can build)
--   {"command":"lord_start_ai","lord":5,"value":1,"build":1}       startAI
--   Dynamic lords (spike S13): {"command":"regions_state"}   every region: owner, settled, type, level, buildings, families (read only)
--   {"command":"lord_relations","lord":3}                    addPawnRelations (a new lord has no relation rows)
--   {"command":"lord_take_region","lord":3,"region":"Goldhof"}  write Region.ownerPawn
--   {"command":"claim_region","target":0,"region":"Eichenhau","finalize":1}  layClaim, then finalizeClaim (target 0 = player, N = lord)
--   {"command":"region_clear_owner","region":"Goldhof"}  write Region.ownerPawn = nil (spike S13 part 2)
--   {"command":"lord_receive_region","lord":3,"region":"Goldhof"}  clear the owner, then the lord claims: the lord builds there
--   {"command":"lord_found_village","lord":3,"region":"Goldhof","type":1,"supply":0}  the lord claims and settles a free region
--   {"command":"settle_region","target":0,"region":"Eichenhau","type":1,"supply":0}  settleRegion (owned region only; x, y, z, outpost optional)
--   Wall commands (spec 14, see mod/shared/HarnessWalls): walls outside the manor system
--   {"command":"wall_state"}                                every wall road (roadType 3 or wallType set): id, wall_name, blueprint, meshes, length, middle (read only)
--   {"command":"road_mode","on":true}                       road tool on or off (clicks with the real mouse then place road points)
--   {"command":"road_commit"}                               commit the drawn road; the answer has its id
--   {"command":"wall_make","road":123,"wall_type":2}        make a committed road a wall: 2 wooden, 3 stone low, 4 stone high
--   {"command":"wall_remove","road":123}                    remove a wall road (PawnCPP:removeRoad)
-- Result: {"id","command","ok","error",...fields of the command}.
-- Commands of other mods do not come through here: each mod serves its own in <run>/modcmd/<ModName>/ (see HarnessCommands).
-- Rules: no eval, only the commands below, an id is handled once, every input is checked before it is used.

local log = require("HarnessLog")
local json = require("HarnessJson")
local autosave = require("HarnessAutosave")
local datatable = require("HarnessDataTable")
local raids = require("HarnessRaids")
local sack = require("HarnessSack")
local loot = require("HarnessLoot")
local battle = require("HarnessBattle")
local ui = require("HarnessUi")
local build = require("HarnessBuild")
local manor = require("HarnessManor")
local lordsCmd = require("HarnessLords")
local walls = require("HarnessWalls")

local VERSION = "18"
local TAG = "HarnessActions"
local POLL_MS = 100
local MAX_PARAGRAPHS = 10
local MAX_NAME_CHARS = 64
local COMMANDS_DIR = log.dir() .. "/commands"

local nextNumber = 1

local function idOf(number) return string.format("%04d", number) end
local function requestPath(number) return COMMANDS_DIR .. "/" .. idOf(number) .. ".json" end
local function resultPath(number) return COMMANDS_DIR .. "/" .. idOf(number) .. ".result.json" end

local function readFile(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local text = f:read("a")
    f:close()
    return text
end

-- Write the result so a reader never sees half of it: write a .tmp file, then rename it.
local function writeResult(number, result)
    local tmp = resultPath(number) .. ".tmp"
    local f = io.open(tmp, "wb")
    if not f then
        log.error(TAG, "cannot write " .. tmp)
        return
    end
    f:write(json.encode(result))
    f:close()
    os.remove(resultPath(number))
    local ok, err = os.rename(tmp, resultPath(number))
    if not ok then log.error(TAG, "cannot rename result: " .. tostring(err)) end
end

local function parseParagraphs(raw)
    local inner = raw:match('"paragraphs"%s*:%s*%[(.-)%]')
    if not inner then return nil end
    local names = {}
    for name in inner:gmatch('"([^"]*)"') do
        if #names >= MAX_PARAGRAPHS then return nil, "too many paragraphs (limit " .. MAX_PARAGRAPHS .. ")" end
        if #name == 0 or #name > MAX_NAME_CHARS or name:find("[^%w_]") then
            return nil, "a paragraph name must be letters, digits and underscore, 1 to " .. MAX_NAME_CHARS .. " characters"
        end
        names[#names + 1] = FName(name)
    end
    if #names == 0 then return nil, "no paragraphs" end
    return names
end

local function parseRequest(raw)
    return {
        id = raw:match('"id"%s*:%s*"([%w_]+)"'),
        command = raw:match('"command"%s*:%s*"([%w_%.]+)"'),
        sender = tonumber(raw:match('"sender"%s*:%s*(%d+)')),
        row = raw:match('"row"%s*:%s*"([%w_ %-]+)"'),
        field = raw:match('"field"%s*:%s*"([%w_]+)"'),
        value = tonumber(raw:match('"value"%s*:%s*(-?[%d%.]+)')),
        squads = tonumber(raw:match('"squads"%s*:%s*(%d+)')),
        count = tonumber(raw:match('"count"%s*:%s*(%d+)')),
        sample = tonumber(raw:match('"sample"%s*:%s*(%d+)')),
        amount = tonumber(raw:match('"amount"%s*:%s*(%d+)')),
        trace = tonumber(raw:match('"trace"%s*:%s*(%d+)')),
        with_loot = tonumber(raw:match('"with_loot"%s*:%s*(%d+)')),
        actors = tonumber(raw:match('"actors"%s*:%s*(%d+)')),
        x = tonumber(raw:match('"x"%s*:%s*(-?[%d%.]+)')),
        y = tonumber(raw:match('"y"%s*:%s*(-?[%d%.]+)')),
        z = tonumber(raw:match('"z"%s*:%s*(-?[%d%.]+)')),
        side = raw:match('"side"%s*:%s*"(%a+)"'),
        method = raw:match('"method"%s*:%s*"(%a+)"'),
        percent = tonumber(raw:match('"percent"%s*:%s*(%d+)')),
        buildings_pct = tonumber(raw:match('"buildings_pct"%s*:%s*(%d+)')),
        stock_pct = tonumber(raw:match('"stock_pct"%s*:%s*(%d+)')),
        people_pct = tonumber(raw:match('"people_pct"%s*:%s*(%d+)')),
        good = tonumber(raw:match('"good"%s*:%s*(%d+)')),
        store = tonumber(raw:match('"store"%s*:%s*(%d+)')),
        manor = tonumber(raw:match('"manor"%s*:%s*(%d+)')),
        job = tonumber(raw:match('"job"%s*:%s*(%d+)')),
        slots = tonumber(raw:match('"slots"%s*:%s*(%d+)')),
        family = tonumber(raw:match('"family"%s*:%s*(%d+)')),
        building = tonumber(raw:match('"building"%s*:%s*(%d+)')),
        pile = tonumber(raw:match('"pile"%s*:%s*(%d+)')),
        table = raw:match('"table"%s*:%s*"(%a+)"'),
        template = raw:match('"template"%s*:%s*"([%w_]+)"'),
        company = raw:match('"company"%s*:%s*"([%w_]+)"'),
        squad = tonumber(raw:match('"squad"%s*:%s*(%d+)')),
        detail = tonumber(raw:match('"detail"%s*:%s*(%d+)')),
        type = tonumber(raw:match('"type"%s*:%s*(%d+)')),
        text = raw:match('"text"%s*:%s*"([^"]*)"'),
        subtext = raw:match('"subtext"%s*:%s*"([^"]*)"'),
        dx = tonumber(raw:match('"dx"%s*:%s*(-?[%d%.]+)')),
        dy = tonumber(raw:match('"dy"%s*:%s*(-?[%d%.]+)')),
        lord = tonumber(raw:match('"lord"%s*:%s*(%d+)')),
        target = tonumber(raw:match('"target"%s*:%s*(%d+)')),
        log = tonumber(raw:match('"log"%s*:%s*(%d+)')),
        name = raw:match('"name"%s*:%s*"([%w_ ]+)"'),
        region = raw:match('"region"%s*:%s*"([%w_]+)"'),
        build = tonumber(raw:match('"build"%s*:%s*(%d+)')),
        finalize = tonumber(raw:match('"finalize"%s*:%s*(%d+)')),
        supply = tonumber(raw:match('"supply"%s*:%s*(%d+)')),
        outpost = raw:match('"outpost"%s*:%s*"([%w_]+)"'),
    }
end

local function inboxCount(pawn)
    return pawn.InBox:GetArrayNum()
end

-- The sender is an AI lord, counted from 1 in the order FindAllOf gives. The recipient is always the player.
local function sendLetter(request, raw)
    local paragraphs, problem = parseParagraphs(raw)
    if not paragraphs then return { ok = false, error = problem or "request has no paragraphs" } end
    local lords = FindAllOf("PawnCPP_AI") or {}
    local sender = request.sender and lords[request.sender]
    if not sender or not sender:IsValid() then
        return { ok = false, error = "no AI lord with sender number " .. tostring(request.sender) .. " (found " .. #lords .. ")" }
    end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local player = engine and engine:IsValid() and engine.playerRef
    if not player or not player:IsValid() then return { ok = false, error = "the player pawn is not loaded" } end
    local before = inboxCount(player)
    sender:sendLetter(player, paragraphs)
    return { ok = true, inbox_before = before, inbox_after = inboxCount(player), paragraphs = #paragraphs }
end

local function autosaveStatus()
    return { ok = true, status = autosave.status() }
end

-- Not a save function: it only restarts the autosave timer with a very long period.
local function disableAutosave()
    local changes, problem = autosave.disable()
    if not changes then return { ok = false, error = problem } end
    return { ok = true, changes = changes }
end

local function datatableInfo(request)
    local info, problem = datatable.info(request.table)
    if not info then return { ok = false, error = problem } end
    return { ok = true, info = info }
end

local function datatableRows(request)
    local rows, problem = datatable.read_all(request.table)
    if not rows then return { ok = false, error = problem } end
    return { ok = true, table = request.table or datatable.DEFAULT_KIND, row_count = #rows, rows = rows }
end

local function datatableRead(request)
    if not request.row or not request.field then return { ok = false, error = "row and field are required" } end
    local values, problem = datatable.read_row(request.row, { request.field }, request.table)
    if not values then return { ok = false, error = problem } end
    return { ok = true, row = request.row, values = values }
end

local function datatableWrite(request)
    if not request.row or not request.field or not request.value then
        return { ok = false, error = "row, field and value are required" }
    end
    local change, problem = datatable.write_number(request.row, request.field, request.value, request.table)
    if not change then return { ok = false, error = problem } end
    return { ok = true, row = request.row, field = request.field, change = change }
end

-- Pop-ups ("Hunger!" and others) are one widget class. The game pauses until the player presses Accept, and it then goes
-- back to the old speed (spec 10, spike S8). `closing` is false while a pop-up waits. IsInViewport and GetIsVisible
-- were false for an open pop-up, so they cannot be used. The handler below is the Blueprint event of the Accept button.
local POPUP_CLASS = "popupMessageWidget_C"
local POPUP_ACCEPT = "BndEvt__popupMessageWidget_Button_Accept_K2Node_ComponentBoundEvent_0_OnButtonReleasedEvent__DelegateSignature"

local function popupWidgets()
    local found = {}
    for _, widget in ipairs(FindAllOf(POPUP_CLASS) or {}) do
        if widget:IsValid() and not widget:GetFullName():find("Default__", 1, true) then found[#found + 1] = widget end
    end
    return found
end

local function popupType(widget)
    local ok, name = pcall(function() return widget.messageType:ToString() end)
    return ok and name or "?"
end

local function popupState()
    local open = {}
    local widgets = popupWidgets()
    for _, widget in ipairs(widgets) do
        if not widget.closing then open[#open + 1] = popupType(widget) end
    end
    return { ok = true, widgets = #widgets, open = open }
end

local function closePopups()
    local closed = {}
    local widgets = popupWidgets()
    for _, widget in ipairs(widgets) do
        if not widget.closing then
            local kind = popupType(widget)
            widget[POPUP_ACCEPT](widget)
            closed[#closed + 1] = kind
        end
    end
    return { ok = true, widgets = #widgets, closed = closed, count = #closed }
end

local COMMANDS = {
    popup_state = popupState,
    close_popups = closePopups,
    ping = function() return { ok = true, version = VERSION } end,
    send_letter = sendLetter,
    autosave_status = autosaveStatus,
    disable_autosave = disableAutosave,
    datatable_info = datatableInfo,
    datatable_read = datatableRead,
    datatable_write = datatableWrite,
    datatable_rows = datatableRows,
    spawn_units = battle.spawn_units,
    battle_state = battle.battle_state,
    clear_battle = battle.clear_battle,
    set_squad_experience = battle.set_squad_experience,
    mercenary_offers = battle.mercenary_offers,
    hire_mercenaries = battle.hire_mercenaries,
    raid_state = raids.raid_state,
    units_census = raids.units_census,
    spawn_raiders = raids.spawn_raiders,
    spawn_elite_raiders = raids.spawn_elite_raiders,
    spawn_bandit_camp = raids.spawn_bandit_camp,
    kill_units = raids.kill_units,
    set_unit_loot = raids.set_unit_loot,
    drop_loot = loot.drop_loot,
    loot_piles = loot.loot_piles,
    recover_loot = loot.recover_loot,
    sack_census = sack.sack_census,
    sack_buildings = sack.sack_buildings,
    sack_goods = sack.sack_goods,
    sack_people = sack.sack_people,
    sack_village = sack.sack_village,
    building_sites = build.building_sites,
    ruin_building = build.ruin_building,
    demolish_ruins = build.demolish_ruins,
    set_site_cost = build.set_site_cost,
    manor_state = manor.manor_state,
    finish_manor_site = manor.finish_site,
    manor_put = manor.manor_put,
    manor_take = manor.manor_take,
    manor_worker_slot = manor.worker_slot,
    manor_assign_worker = manor.assign_worker,
    manor_unassign_workers = manor.unassign_workers,
    manor_worker_state = manor.worker_state,
    show_message = ui.show_message,
    read_message = ui.read_message,
    list_messages = ui.list_messages,
    lords_state = lordsCmd.lords_state,
    lord_declare_war = lordsCmd.lord_declare_war,
    lord_declare_peace = lordsCmd.lord_declare_peace,
    lord_set_influence = lordsCmd.lord_set_influence,
    lord_challenge = lordsCmd.lord_challenge,
    lord_claim = lordsCmd.lord_claim,
    lord_spawn_army = lordsCmd.lord_spawn_army,
    spawn_ai_lord = lordsCmd.spawn_ai_lord,
    lord_start_ai = lordsCmd.lord_start_ai,
    regions_state = lordsCmd.regions_state,
    lord_relations = lordsCmd.lord_relations,
    lord_take_region = lordsCmd.lord_take_region,
    claim_region = lordsCmd.claim_region,
    settle_region = lordsCmd.settle_region,
    lord_receive_region = lordsCmd.lord_receive_region,
    lord_found_village = lordsCmd.lord_found_village,
    region_clear_owner = lordsCmd.region_clear_owner,
    wall_state = walls.wall_state,
    road_mode = walls.road_mode,
    road_commit = walls.road_commit,
    wall_make = walls.wall_make,
    wall_remove = walls.wall_remove,
}

local function runCommand(number, raw)
    local request = parseRequest(raw)
    local result
    local handler = request.command and COMMANDS[request.command]
    if not request.id or request.id ~= idOf(number) then
        result = { ok = false, error = "request id must be " .. idOf(number) }
    elseif not handler then
        result = { ok = false, error = "unknown command: " .. tostring(request.command) }
    else
        local ok, answer = pcall(handler, request, raw)
        result = ok and answer or { ok = false, error = tostring(answer) }
    end
    result.id = idOf(number)
    result.command = request.command
    writeResult(number, result)
    log.info(TAG, "command " .. idOf(number) .. " " .. tostring(request.command) .. " ok=" .. tostring(result.ok))
end

local function skipHandled()
    while readFile(resultPath(nextNumber)) do nextNumber = nextNumber + 1 end
end

skipHandled()

LoopAsync(POLL_MS, function()
    local raw = readFile(requestPath(nextNumber))
    if not raw then return false end
    local number = nextNumber
    nextNumber = nextNumber + 1
    ExecuteInGameThread(function() log.try(TAG, runCommand, number, raw) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. ", waiting for " .. requestPath(nextNumber))
