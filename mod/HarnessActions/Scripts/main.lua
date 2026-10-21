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
--   {"command":"load_pak_blueprint","name":"BM_HarnessCamp"}   spec 18: load /Game/HarnessMod/<name> of a mod pak with the asset registry (LoadAsset cannot)
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
--   {"command":"unit_probe","squad":32,"call":"equipTradeWagon"}   spike (spec 29): call one allow-listed no-parameter function on a unit
--   {"command":"prop_spawn","prop":"Resource_BigCart_C","count":3,"dx":0,"dy":0,"step":400}  spike (spec 29): spawn prop actors near the player; prop_clear destroys them; squad_positions reads a squad
--   {"command":"battle_state","detail":1}                      living units, experience and casualties of the squads that this mod spawned or hired
--   {"command":"clear_battle","side":"bandit"}                 kill the units of those squads (of one side if "side" is given) and forget them
--   {"command":"unit_stats","side":"bandit"}                   mean att, def, block, armorPierce, morale of the living units of the registry (spec 25)
--   {"command":"set_unit_stat","side":"player","field":"def","value":0}  write one SMUnit stat on the living units of a side, read back (spec 25)
--   {"command":"combat_hook","mode":"start"}                 observe-only hook on SMUnit:CombatHit; start, stop or read the call counts (spec 25)
--   {"command":"tune_state"}                                    per side (player, bandit, ai_lord, other) and squad: living units, mean stats, active overrides (spec 28)
--   {"command":"tune_set","side":"bandit","field":"att","value":3}  write a stat on ALL living units of a side (or "squad": id), keep it as an override, re-apply every 2 s (spec 28)
--   {"command":"tune_reset","side":"bandit","field":"att"}      remove overrides (all if no argument) and restore the original values (spec 28)
--   {"command":"tune_apply"}                                     run one override pass now (spec 28)
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
--   {"command":"battlefield_anchor","lord":1,"target":0,"x":0,"y":0,"delay_ms":500}   move all battlefield_BP_C to the anchor (x,y, or the manor of "region" / the target region), challenge when "lord" is set, restore after delay_ms
--   {"command":"battlefield_state"}                          where the battlefield actors are now (read only)
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
--   Policy commands (spec 16, see mod/shared/HarnessPolicies): the edicts of the player's region
--   {"command":"policy_state"}                              policies in the slots, signed ids, available ids, slot count, approval and its factors, silver, influence (read only)
--   {"command":"policy_enact","policy":12,"slot":0}         PawnCPP:enactPolicy; refused when the id is not available or the slot is outside the slot count
--   {"command":"policy_sign","policy":12,"signed":false}   Region:setPolicySigned (the call the policy widget uses)
--   {"command":"menu_probe_show","policy":12,"x":300,"y":300}   spike: put one game policy widget (policyWidget_C) on the screen; menu_probe_read polls its button; menu_probe_hide removes it
--   Bandit negotiation (spec 15, see mod/shared/HarnessBandits):
--   {"command":"bandit_state"}                              families, bandit units, silver, influence, relation tags with the bandit lord (read only)  (regions[] also give vacant_slots)
--   {"command":"bandit_tag","tag":"attacking","remove":0}  add (or remove) a relation tag between the player and the bandit lord
--   {"command":"bandit_letter","paragraphs":["raider_suggestSettle"]}   PawnCPP:sendLetter from the player to the bandit lord
--   {"command":"settle_raiders"}                            MLCheatManager:SettleRaiders (developer cheat)
--   Reverse direction (spec 15, homeless rebellion, see implementation-notes/homeless-rebellion.md):
--   {"command":"bandit_spawn_at","x":0,"y":0,"z":0,"template":"Brigands","count":1}   bandit squads at a chosen point (spawnArmy, owner = bandit lord)
--   {"command":"bandit_turn","count":3,"source":"squad"}  SMUnit:turnToBandit on units of player squads made by spawn_units ("source":"family": family members)
--   {"command":"homeless_rebel","count":2,"families_per_squad":1,"template":"Brigands","mode":"home"}   remove families, then bandits appear at their homes ("mode":"raid": a real raid that targets the home)
--   {"command":"rebel_raid_rally","count":2}   remove families, then one real raid aimed at a forest spot; the raiders stand at the AI waypoint for about 100 to 150 game seconds, then attack. The answer has the squad ids, the spot and the families before and after
--   {"command":"bandit_kill_squads","squad":41,"count":2}   SMUnit:just_die on every living bandit unit of squads 41, 42 (to remove a raid and keep other squads)
--   Save and game setup (specs 24 and 26):
--   {"command":"save_game","label":"x"}                     guarded harness save (spec 24, see harness/runlib/harness_save.py)
--   {"command":"game_setup_state"}                          read the game start settings and the victory goal (spec 26)
--   {"command":"game_setup_set_goal"}                       set a victory goal (spec 26)
--   Housing (spec 15, see mod/shared/HarnessHousing):
--   {"command":"upgrade_stat","type":117}                      number fields of one DT_Upgrades row (spec 23, read only)
--   {"command":"building_stat","type":87}                   scalar fields of the buildingStats row of one building type (read only)
--   {"command":"building_stat_vector_write","type":87,"field":"occupantTypes","component":"Y","value":5}   UNSAFE test command (needs HARNESS_ALLOW_UNSAFE=1): write one component of a Vector4 field of a buildingStats row, in memory
--   {"command":"housing_state"}                             player region: families, homeless, living and vacant slots, tents, residential buildings (read only)
--   {"command":"accommodate_homeless"}                      Region:accomodateHomelessFamilies(nil); the answer has the housing before and after
--   {"command":"family_state"}                              housing numbers with approval and public order, and the ids of the housed families (read only)
--   {"command":"family_census"}                             one row per family (living members, roles, familyHome) and one row per home or tent with its occupant family ids (spec 15 #61; read only)
--   {"command":"member_fields","count":0}                   property names (and plain values) of one member of the family with that zero-based index (spec 15 #61; read only)
--   {"command":"family_eject","count":2,"suppress":true,"home":"none"}   Region:SetFamilyHome(id, nil, suppress): housed families leave their homes ("home":"tent": into the first homeless tent) (spec 15 part 7)
--   {"command":"family_add","count":1,"adult":false}                      a villager leaves a family of 2 or more and starts a new family (Region:AddNewFamily); it has no home
--   {"command":"tent_find_spot"}                           up to 5 free spots for a tent (x, y, z) around the village centre; it does not place anything (read only)
--   {"command":"forest_spot","min_dist":15000,"max_dist":40000}   up to 5 dense tree cells of the player region, best first (Resource actors with resType "tree"; read only)
--   {"command":"plot_field_shift","dx":3000,"dy":0,"plots":true,"commit":true}   test only: move the drawn, closed plot outline of the pawn (plots: also extractedPlots), then commit it
--   {"command":"plot_upgrade","upgrade":12,"slot":0,"extension":false}   spike: PawnCPP:addUpgradeRequest (or addExtensionChangeRequest) on the building under the mouse
--   {"command":"plot_upgrade","upgrade":13,"type":97}   same, on the first own master of that building type (no mouse)
--   {"command":"building_assign_worker","type":125}         put one family without a workplace (or "family":N) to work in the first own building of that type (issue 104, no mouse)
--   Composite parts (spec 18, see mod/shared/HarnessParts):
--   {"command":"master_parts","building":123,"limit":5}      parts and extensions of one building master (or "type":3: the first built one; read only)
--   {"command":"master_artisan","type":3}                  spec 31: artisan job, canMake, workers and extension types of a master (read only); master_parts also takes "ext_limit":N for extension part rows
--   {"command":"master_artisan_set","type":3,"job":14}      UNSAFE spec 31: write artisanJob (or "extension_type":N: call changeArtisanType) on a master
--   {"command":"master_site","type":483}                    state of a site, built or not: Region, owner, goods, builders (issue 94, read only)
--   {"command":"master_set_region","type":483}              write site.Region = the region of the player pawn (issue 94)
--   {"command":"master_finish","type":483}                  write Data.constructed = true on a site, read it back (issue 94)
--   {"command":"master_part_remove","building":123,"index":1,"mode":"hide"}   UNSAFE: hide, destroy or unlink one part (needs HARNESS_ALLOW_UNSAFE=1)
--   {"command":"master_part_add","building":123,"from":1,"dx":300}   UNSAFE: spawn a copy of part "from" and append it to the part list
--   Walls (spec 14, see mod/shared/HarnessWalls):
--   {"command":"wall_pieces","road":123,"step":200}         spawn blocking palisade pieces (GhostStaticMeshActor, type 470) along a road
--   {"command":"wall_pieces_clear","road":123}              destroy the pieces that wall_pieces made for that road
--   {"command":"path_state"}                                size of the global obstacle list and the path debug flag (read only)
--   {"command":"building_stat","kind":470}                  spike, read only: scalar fields of one buildingStats row (with "kind": the spec 14 reader; with "type": the spec 15 reader)
--   {"command":"building_health","building":123}            spike, read only: type, hp, maxHp, onFire, fireAmt, rubble, built of one building
--   {"command":"manor_blueprint_add","type":58,"x":0,"y":0,"z":0,"yaw":0,"commit":true}   spike (#63): add a manor planner blueprint (mesh actor tagged bType_<type>) without the mouse, then convertBlueprintsToBuildings
--   {"command":"mesh_users","mesh":"PalisadeWall"}          spike, read only: mesh components that use a mesh, grouped by owner class
--   {"command":"wagen_state"} / {"command":"wagen_apply","manor":123,"wall_mesh":"/Game/HarnessMod/..","keep_mesh":".."} / {"command":"wagen_revert"}   spike (spec 32 part 2): set the wall and keep meshes of ONE manor; revert restores them
--   {"command":"mesh_material_swap","mesh":"<name part>","near_x":0,"near_y":0,"mode":"borrow"}   spike: our model draws with a game material ("lend": a game building draws with ours)
--   {"command":"mesh_material_params","mesh":"<name part>","near_x":0,"near_y":0,"scalars":"a=1,b=0"}   spike: live material parameters of one mesh component
--   {"command":"mesh_actors","mesh":"PalisadeWallNarrow"}   spike (spec 32), read only: owner class and position of the actors whose mesh matches
--   {"command":"steer_state","squad":41}                    spike #59, read only: owner side, living units, centre and mean unit target of a squad
--   {"command":"steer_move","squad":41,"x":0,"y":0,"half_width":300}   spike #59: PawnCPP:formALineArmy of the owner pawn, one squad, a line across the way to the point
--   {"command":"steer_hook","functions":"/Script/ManorLords.PawnCPP:formALineArmy,/Script/ManorLords.PawnCPP:selectSquad"}   spike #59: record the calls of these functions; steer_hook_log reads (and clears) them
--   {"command":"lead_unit_gear","squad":41} / {"command":"lead_stance","squad":41,"stance":"aggressive"} / {"command":"lead_spawn_unit","lord":1,"template":"spearMilitia","count":2} / {"command":"lead_squad_camp","lord":1}   spike (#280): GetEquippedID of a squad, SetBehaviourStance, spawnCompleteUnit, Squad.camp fields
--   {"command":"lead_mesh_list"} / {"command":"lead_mesh_swap","component":"<full name>","mesh":"<object path>"} / {"command":"lead_mesh_swap","component":"<full name>","restore":true}   spike (#280): building mesh swap with SetStaticMesh
--   Unsafe spike commands: refused unless the game runs with HARNESS_ALLOW_UNSAFE=1 (test games only)
--   {"command":"construction_complete","building":123}      PawnCPP:constructionComplete on one building
--   {"command":"path_obstacles_clear"}                      empty the global obstacle list (the next squad spawn crashed the game)
--   {"command":"building_stat_write","kind":30,"field":"isModule","value":true}  write one buildingStats field in memory
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
local policies = require("HarnessPolicies")
local bandits = require("HarnessBandits")
local housing = require("HarnessHousing")
local parts = require("HarnessParts")
local steer = require("HarnessSteer")
local battlefield = require("HarnessBattlefield")
local tune = require("HarnessTune")
local garrison = require("HarnessGarrison")
local gameSetup = require("HarnessGameSetup")
local harnessSave = require("HarnessSave")
local encampment = require("HarnessEncampment")
local wagenburg = require("HarnessWagenburg")
local leads = require("HarnessLeads")

local VERSION = "59"
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
        goal = tonumber(raw:match('"goal"%s*:%s*(%d+)')),
        consume = tonumber(raw:match('"consume"%s*:%s*(%d+)')),
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
        half_width = tonumber(raw:match('"half_width"%s*:%s*(-?[%d%.]+)')),
        formation = raw:match('"formation"%s*:%s*"([%w_]+)"'),
        functions = raw:match('"functions"%s*:%s*"([^"]*)"'),
        clear = ({ ["true"] = true, ["false"] = false })[raw:match('"clear"%s*:%s*(%a+)') or ""],
        detail = tonumber(raw:match('"detail"%s*:%s*(%d+)')),
        type = tonumber(raw:match('"type"%s*:%s*(%d+)')),
        text = raw:match('"text"%s*:%s*"([^"]*)"'),
        subtext = raw:match('"subtext"%s*:%s*"([^"]*)"'),
        dx = tonumber(raw:match('"dx"%s*:%s*(-?[%d%.]+)')),
        dy = tonumber(raw:match('"dy"%s*:%s*(-?[%d%.]+)')),
        delay_ms = tonumber(raw:match('"delay_ms"%s*:%s*(-?%d+)')),
        lord = tonumber(raw:match('"lord"%s*:%s*(%d+)')),
        target = tonumber(raw:match('"target"%s*:%s*(%d+)')),
        log = tonumber(raw:match('"log"%s*:%s*(%d+)')),
        name = raw:match('"name"%s*:%s*"([%w_ ]+)"'),
        region = raw:match('"region"%s*:%s*"([%w_]+)"'),
        build = tonumber(raw:match('"build"%s*:%s*(%d+)')),
        finalize = tonumber(raw:match('"finalize"%s*:%s*(%d+)')),
        supply = tonumber(raw:match('"supply"%s*:%s*(%d+)')),
        tag = raw:match('"tag"%s*:%s*"([%w_]+)"'),
        remove = tonumber(raw:match('"remove"%s*:%s*(%d+)')),
        outpost = raw:match('"outpost"%s*:%s*"([%w_]+)"'),
        policy = tonumber(raw:match('"policy"%s*:%s*(%d+)')),
        slot = tonumber(raw:match('"slot"%s*:%s*(%d+)')),
        save_slot = raw:match('"save_slot"%s*:%s*"(saveGame_%d+)"'), -- spec 24, checked again by HarnessSave
        save_name = raw:match('"save_name"%s*:%s*"([%w _%-]+)"'),
        signed = ({ ["true"] = true, ["false"] = false })[raw:match('"signed"%s*:%s*(%a+)') or ""],
        mode = raw:match('"mode"%s*:%s*"(%a+)"'),
        source = raw:match('"source"%s*:%s*"(%a+)"'),
        -- spike #280: these four fields were missing, so runs 1 to 5 of probe-lead-stance never set a stance
        stance = raw:match('"stance"%s*:%s*"(%a+)"'),
        component = raw:match('"component"%s*:%s*"([^"]*)"'),
        mesh = raw:match('"mesh"%s*:%s*"([^"]*)"'),
        restore = ({ ["true"] = true, ["false"] = false })[raw:match('"restore"%s*:%s*(%a+)') or ""],
        families_per_squad = tonumber(raw:match('"families_per_squad"%s*:%s*(%d+)')),
        min_dist = tonumber(raw:match('"min_dist"%s*:%s*(%d+)')),
        max_dist = tonumber(raw:match('"max_dist"%s*:%s*(%d+)')),
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

-- Specs 14 and 15 each added a building_stat reader: spec 14 takes "kind", spec 15 takes "type". Keep both request forms.
local function buildingStat(request, raw)
    if type(raw) == "string" and raw:match('"kind"%s*:') then return walls.building_stat(request, raw) end
    return housing.building_stat(request, raw)
end

-- Spec 18: load a Blueprint of a mod pak (/Game/HarnessMod/<name>) so that native code can find its class by path.
-- LoadAsset does not load pak assets. The asset registry call does (spec 16 pak-widget-spike.md).
local PAK_PACKAGE = "/Game/HarnessMod"
local function loadPakBlueprint(_, raw)
    local name = type(raw) == "string" and raw:match('"name"%s*:%s*"([%w_]+)"')
    if not name then return { ok = false, error = "name must be letters, digits and underscores" } end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if not registry or not registry:IsValid() then return { ok = false, error = "AssetRegistryHelpers not found" } end
    local classPath = PAK_PACKAGE .. "/" .. name .. "." .. name .. "_C"
    local data = {
        PackageName = FName(PAK_PACKAGE .. "/" .. name), PackagePath = FName(PAK_PACKAGE), AssetName = FName(name),
        AssetClassPath = { PackageName = FName("/Script/Engine"), AssetName = FName("Blueprint") },
    }
    local ok, err = pcall(function() return registry:GetAsset(data) end)
    if not ok then return { ok = false, error = "GetAsset: " .. tostring(err) } end
    local found = StaticFindObject(classPath)
    local loaded = found ~= nil and found:IsValid()
    -- Why: a class that only the asset registry call loaded can be freed by the garbage collector. Try to keep it.
    local rooted = false
    if loaded then rooted = pcall(function() found:AddToRoot() end) end
    return { ok = loaded, rooted = rooted, class = classPath, loaded = loaded, error = (not loaded) and "class not found after GetAsset; is the pak installed?" or nil }
end

-- Spec 18 spike: spawn the class of a BM_ Blueprint once (our own actor), list its components, destroy it.
-- Why: native code made no parts from a pak class. This shows what an instance holds.
local function spawnProbe(_, raw)
    local classPath = type(raw) == "string" and raw:match('"class"%s*:%s*"([%w_/%.]+)"')
    if not classPath then return { ok = false, error = "class must be a path like /Game/HarnessMod/BM_X.BM_X_C" } end
    local class = StaticFindObject(classPath)
    if not class or not class:IsValid() then return { ok = false, error = "class not loaded: " .. classPath } end
    local world = FindFirstOf("PlayerController"):GetWorld()
    local okSpawn, actor = pcall(function() return world:SpawnActor(class, { X = 0, Y = 0, Z = 100000 }, { Pitch = 0, Yaw = 0, Roll = 0 }) end)
    if not okSpawn or not actor or not actor:IsValid() then return { ok = false, error = "spawn failed: " .. tostring(actor) } end
    local out = { ok = true, actor = tostring(actor:GetFName():ToString()), components = {} }
    local okAll, all = pcall(function() return actor:K2_GetComponentsByClass(StaticFindObject("/Script/Engine.StaticMeshComponent")) end)
    if okAll and all then
        for i = 1, #all do
            local c = all[i]
            if c.get then c = c:get() end
            local mesh = pcall(function() return c.StaticMesh end) and c.StaticMesh
            out.components[#out.components + 1] = tostring(c:GetFName():ToString()) .. " mesh=" .. tostring(mesh and mesh:IsValid() and mesh:GetFName():ToString() or "none")
        end
    else
        out.components_error = tostring(all)
    end
    pcall(function() actor:K2_DestroyActor() end)
    return out
end

local COMMANDS = {
    popup_state = popupState,
    close_popups = closePopups,
    load_pak_blueprint = loadPakBlueprint,
    spawn_probe = spawnProbe,
    ping = function() return { ok = true, version = VERSION } end,
    send_letter = sendLetter,
    autosave_status = autosaveStatus,
    save_game = harnessSave.save_game, -- the only save call in the repo; guarded by harness/runlib/harness_save.py
    disable_autosave = disableAutosave,
    datatable_info = datatableInfo,
    datatable_read = datatableRead,
    datatable_write = datatableWrite,
    datatable_rows = datatableRows,
    spawn_units = battle.spawn_units,
    battle_state = battle.battle_state,
    clear_battle = battle.clear_battle,
    set_squad_experience = battle.set_squad_experience,
    unit_stats = battle.unit_stats,
    unit_probe = battle.unit_probe,
    prop_spawn = battle.prop_spawn,
    prop_clear = battle.prop_clear,
    squad_positions = battle.squad_positions,
    set_unit_stat = battle.set_unit_stat,
    combat_hook = battle.combat_hook,
    tune_state = tune.tune_state,
    tune_set = tune.tune_set,
    tune_reset = tune.tune_reset,
    tune_apply = tune.tune_apply,
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
    battlefield_anchor = battlefield.battlefield_anchor,
    battlefield_state = battlefield.battlefield_state,
    lord_claim = lordsCmd.lord_claim,
    lord_spawn_army = lordsCmd.lord_spawn_army,
    spawn_ai_lord = lordsCmd.spawn_ai_lord,
    lord_start_ai = lordsCmd.lord_start_ai,
    regions_state = lordsCmd.regions_state,
    lord_relations = lordsCmd.lord_relations,
    lord_take_region = lordsCmd.lord_take_region,
    claim_region = lordsCmd.claim_region,
    game_setup_state = gameSetup.game_setup_state,
    game_setup_set_goal = gameSetup.game_setup_set_goal,
    settle_region = lordsCmd.settle_region,
    lord_receive_region = lordsCmd.lord_receive_region,
    lord_found_village = lordsCmd.lord_found_village,
    region_clear_owner = lordsCmd.region_clear_owner,
    wall_state = walls.wall_state,
    road_mode = walls.road_mode,
    road_commit = walls.road_commit,
    wall_make = walls.wall_make,
    wall_remove = walls.wall_remove,
    policy_state = policies.policy_state,
    policy_enact = policies.policy_enact,
    policy_sign = policies.policy_sign,
    policy_enact_sweep = policies.policy_enact_sweep,
    menu_probe_show = policies.menu_probe_show,
    menu_probe_read = policies.menu_probe_read,
    menu_probe_hide = policies.menu_probe_hide,
    bandit_state = bandits.bandit_state,
    bandit_tag = bandits.bandit_tag,
    bandit_letter = bandits.bandit_letter,
    settle_raiders = bandits.settle_raiders,
    bandit_mark = bandits.bandit_mark,
    bandit_track = bandits.bandit_track,
    bandit_spawn_at = bandits.bandit_spawn_at,
    bandit_turn = bandits.bandit_turn,
    homeless_rebel = bandits.homeless_rebel,
    rebel_raid_rally = bandits.rebel_raid_rally,
    bandit_kill_squads = bandits.bandit_kill_squads,
    building_stat = buildingStat,
    upgrade_stat = housing.upgrade_stat,
    building_stat_vector_write = housing.building_stat_vector_write,
    master_parts = parts.master_parts,
    master_artisan = parts.master_artisan,
    master_artisan_set = parts.master_artisan_set,
    master_site = parts.master_site,
    master_set_region = parts.master_set_region,
    master_finish = parts.master_finish,
    master_part_remove = parts.master_part_remove,
    master_part_add = parts.master_part_add,
    wagen_state = wagenburg.wagen_state,
    wagen_apply = wagenburg.wagen_apply,
    wagen_revert = wagenburg.wagen_revert,
    encampment_sites = encampment.encampment_sites,
    encampment_regions = encampment.encampment_regions,
    encampment_spawn = encampment.encampment_spawn,
    encampment_list = encampment.encampment_list,
    encampment_remove = encampment.encampment_remove,
    housing_state = housing.housing_state,
    accommodate_homeless = housing.accommodate_homeless,
    family_state = housing.family_state,
    family_census = housing.family_census,
    member_fields = housing.member_fields,
    family_eject = housing.family_eject,
    family_add = housing.family_add,
    tent_find_spot = housing.tent_find_spot,
    forest_spot = housing.forest_spot,
    plot_field_shift = housing.plot_field_shift,
    plot_field_place = housing.plot_field_place,
    plot_upgrade = housing.plot_upgrade,
    building_assign_worker = housing.building_assign_worker,
    wall_pieces = walls.wall_pieces,
    wall_pieces_clear = walls.wall_pieces_clear,
    path_state = walls.path_state,
    building_health = walls.building_health,
    manor_blueprint_add = walls.manor_blueprint_add,
    manor_planner = walls.manor_planner,
    mesh_users = walls.mesh_users,
    mesh_actors = walls.mesh_actors,
    mesh_material_params = walls.mesh_material_params,
    mesh_material_swap = walls.mesh_material_swap,
    construction_complete = walls.construction_complete,
    path_obstacles_clear = walls.path_obstacles_clear,
    building_stat_write = walls.building_stat_write,
    steer_state = steer.steer_state,
    steer_move = steer.steer_move,
    steer_select = steer.steer_select,
    steer_cursor = steer.steer_cursor,
    steer_mouse3d = steer.steer_mouse3d,
    steer_rmb = steer.steer_rmb,
    steer_hook = steer.steer_hook,
    steer_hook_log = steer.steer_hook_log,
    lead_unit_gear = leads.lead_unit_gear,
    lead_stance = leads.lead_stance,
    lead_spawn_unit = leads.lead_spawn_unit,
    lead_squad_camp = leads.lead_squad_camp,
    lead_mesh_list = leads.lead_mesh_list,
    lead_mesh_swap = leads.lead_mesh_swap,
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
log.try(TAG, garrison.install)

LoopAsync(POLL_MS, function()
    local raw = readFile(requestPath(nextNumber))
    if not raw then return false end
    local number = nextNumber
    nextNumber = nextNumber + 1
    ExecuteInGameThread(function() log.try(TAG, runCommand, number, raw) end)
    return false
end)

log.say(TAG, "loaded version " .. VERSION .. ", waiting for " .. requestPath(nextNumber))
