-- Feature switches and tunables (balance values). One table for each feature, named like the feature.
-- Put every balance value here, not in the feature logic.
return {
    example = { enabled = true },
    -- Key registry of ModState for the mod "invasion". The "selftest_*" keys exist for the scenarios of M01.
    -- A later feature registers its own keys with ModState.open("invasion", "pawn"):register(...).
    mod_state = {
        enabled = true,
        keys = {
            { key = "selftest_int", kind = "integer", default = 0 },
            { key = "selftest_flag", kind = "boolean", default = false },
            { key = "selftest_text", kind = "string", default = "none" },
        },
    },
    -- M02 invasion, iterations 01 and 02 (the tick runs at each season change). First guesses from the M00 balance targets.
    invasion = {
        enabled = true,
        levels = { yearly = 2, great = 2, vassal = 2 },     -- update-raid-difficulty-levels: start value of the level of each raid type, 0 (off) to 3 (hard); the owner default is 2 (medium), also before the settings menu applies anything.
        yearly = {                                           -- update-raid-clock-yearly: no raid in game year 1, then one raid a year
            chance_by_season = { 25, 33, 50, 100 },          -- percent at the season change, first to fourth season of the year (owner decision 2026-10-21)
            season_days = 90,                                -- the raid comes 1 to this many game days after the successful roll
        },
        size_multipliers = { small = 1, medium = 2, large = 3 }, -- squads = multiplier x level of the raid type
        squad_units = 18,                                    -- units in one squad of spawnRaiders
        base_timer_floor = 300,                              -- the mod lifts the base game raid timer when it falls under this
        base_timer_refill = 700,
        raid_banner_days = 30,                               -- update-raid-banners: the one banner of a subjugation or player raid shows this many game days before the raid
        great_raid = {                                       -- the great raid starts at the first day of a game year (4 season changes a year)
            start_year = 10,                                 -- game year of the first wave (owner decision 2026-10-22)
            warning_years = 3,                               -- one clock banner at the start of each of this many years before the start year
            season_estimate_days = 92,                       -- estimate of the days left to the start year (a season has about 91 days; the real day replaces it)
            relief_full_squads = 15,                         -- relief army at difficulty 1 (decisions 17, 26)
            wave_squads = 15,                                -- a large army (decision 16)
            -- M02 iteration 06: the waves, the relief army and the final battle. All values are TBD for playtests.
            wave_gap_days = 10,                              -- game days between two waves
            relief_delay_days = 10,                          -- game days from the last wave to the relief army and the final battle
            final_squads = 25,                               -- "very large" (more than the 15 of a large army); not scaled by difficulty
            final_tier_difficulty = 2,                       -- the tier mix of the final army (roles table of this difficulty)
            relief_templates = { "militiaFoot", "spearMilitia", "bowMilitia", "crossbowMilitia" }, -- the liege squads, cycled
            relief_offset = { x = 0, y = 2500 },             -- the relief army appears this far from the player pawn
        },
        -- M02 iteration 03: the subjugation raid (major). The yearly roll plans it as the second raid. Values are TBD for playtests.
        subjugation = {
            enabled = true,
            size_class = 3,                                  -- large: squads = 3 x difficulty (TBD, "major" has no size rule in M00)
        },
        poll_ms = 300,                                       -- real time between two checks of the game day
        seed = nil,                                          -- nil: seed from the clock
        -- M05 iteration 02: Hussite roles of a raid (decision 7). All weights and shares are TBD for playtests.
        -- Templates are rows of DT_UnitTemplates, checked in the real game (openspec/changes/archive/2026-10-16-legacy-m05-unit-balance/iterations/02-hussite-roles.md).
        roles = {
            enabled = true,                  -- false: the raid is spawned with spawnRaiders (Brigands only, 18 units a squad)
            templates = {
                melee = {
                    { "Brigands", "spearMilitia" },             -- tier I
                    { "militiaFoot", "mercenary_infantry" },    -- tier II: sword and axe infantry
                    { "retinue_tier3", "brigandPolearms" },     -- tier III: retinue and poleaxe infantry
                },
                ranged = {
                    { "bowMilitia", "brigandArchers" },                 -- tier I: bows
                    { "crossbowMilitia", "mercenary_crossbowmen" },     -- tier II: crossbows
                },
            },
            template_units = {               -- units in one squad, measured with spawnArmy
                Brigands = 18, spearMilitia = 32, militiaFoot = 32, mercenary_infantry = 36, retinue_tier3 = 36, brigandPolearms = 36,
                bowMilitia = 32, brigandArchers = 36, crossbowMilitia = 32, mercenary_crossbowmen = 36,
            },
            ranged_share = 0.25,             -- part of the squads that is ranged
            crossbow_share = { 0.0, 0.5, 0.75 },                 -- part of the ranged squads that is tier II, by difficulty
            melee_tier_weights = { { 70, 30, 0 }, { 40, 40, 20 }, { 20, 40, 40 } }, -- melee tier I, II, III, by difficulty
            lord_army = {                    -- the raid is the army of an AI lord at war with the player (M03.02); false: bandit squads
                enabled = true,
                lord_name = "Hussite Raiders",
                start_dy = -50000,           -- the army appears this far from the player pawn (HarnessLords limit 60000)
            },
            raid_spawn_y = -88900,           -- map edge where spawnRaiders put raiders (spec 15 runs). x is the x of the player pawn.
        },
    },
    -- M03 raid_behavior. Steers the Hussite raids. A native raid is only tracked.
    raid_behavior = {
        enabled = true,
        poll_ms = 1000,         -- real time between two looks at the raiders
        pit_poll_ms = 1000,     -- real time between two looks at the corpse pit (change add-corpse-pit-loot)
        slow_every = 5,         -- the building scan and the AI log scan run every Nth look (they read many objects)
        carry_cap = 10,         -- most goods a Hussite raid plunders for each raider at its start (M00: Hussite grain 10). It is also the loot goal of a Hussite raid. Other raids are not capped.
        exit_y = -85000,       -- a raider that vanishes at or below this y walked off the map. It keeps its loot.
        -- M03 iteration 02: a role raid (spawnArmy squads) leaves like a native raid. All values are TBD for playtests.
        plunder = {                 -- the plunder tick of a lord raid: goods leave the stores while the army stands at the manor
            battle_radius = 4000,   -- a raider counts as inside this far from the manor (the army stood within 1300 in run 20261018-035856-248b)
            per_unit_day = 1,       -- goods taken for each raider inside, each game day. The goal is leave.loot_per_raider for each raider.
        },
        -- Change add-raid-storage-tiers. Store tiers by EBuildingType: tier 1 (storehouse 6, granary 72) can be robbed by the mod, tier 2 (the manor modules) never.
        store_tiers = { [6] = 1, [72] = 1, [50] = 2, [57] = 2, [58] = 2, [81] = 2, [82] = 2, [83] = 2, [95] = 2, [98] = 2 },
        steal = {                   -- baron (lord) raid steal: a raider farther than threshold from the battle marker takes goods from tier 1 stores
            threshold = 20000,      -- game units (1 unit = 1 cm, so 200 m; owner 2026-10-20). The army fights about 14000 from the marker.
            rate = 10,              -- goods for each stealing raider, each game day
            goals = { plunder = 100, great = 300 }, -- most goods one raid steals, by raid kind (small and large raid; no scaling by difficulty yet)
        },
        leave = {
            enabled = true,
            loot_per_raider = 4,   -- leaves when the loot taken is this much for each raider of the start (native raiders carry 4 to 5)
            loss_share = 0.5,       -- leaves when this share of the raiders died
            max_days = 25,          -- leaves this many game days after the spawn (native raids ended on day 12 to 19)
        },
    },
    -- M05 unit_balance, iteration 01. Unarmored units take more damage (spec 25: def 0 and block 0 doubled the losses of militia).
    unit_balance = {
        enabled = true,
        poll_ms = 4000,                -- real time between two looks for new units
        recheck_every = 10,            -- a full re-read of known units runs every Nth pass, or when the unit count changes
        armored_def_min = 10,          -- a unit with def below this is unarmored (Brigands about 3, militia 5 to 7, mail 10, retinue 62)
        unarmored_def_factor = 0.0,    -- new def = def x factor, for an unarmored unit
        unarmored_block_factor = 0.0,  -- new block = block x factor
        militia_roles = { 0, 2 },      -- EUnitRole Husband and Son: units of the player pawn with these roles are militia
        -- M05 iteration 03: armor needs a weapon to pay off (spec 25: armor alone did not win). Values TBD by the A/B.
        heavy_def_min = 40,            -- units with this def or more (retinue 62) are heavy: no weapon bonus
        armored_att_factor = 1.5,      -- new att = att x factor, for an armored unit (def from armored_def_min up to heavy_def_min)
        armored_pierce_add = 2,        -- new armorPierce = armorPierce + amount (poleaxe infantry has 2)
        -- M05 iteration 04. Spec: openspec/changes/archive/2026-10-16-legacy-m05-unit-balance/iterations/04-counters-veterancy.md. All values TBD by the A/B.
        reach_min = 110, reach_max = 125, -- units with a weapon reach in this band are pike units (spears 120; swords 65, villagers 100, axes 130)
        reach_att_add = 1.0,           -- att + amount for a pike unit: spearMilitia att 4 reaches militiaFoot att 5 (data: spear lost 0 of 5 against swords)
        veterancy = {
            enabled = true,
            step = 1.0,                -- experience points for one tier (a fight gives about 0.5 to 1.3 to the mean unit, spike C2)
            max_tier = 5,
            att_per_tier = 0.1,        -- att and def are scaled by 1 + tier x this value (0.04 gave no effect in the A/B)
            def_per_tier = 0.1,
            every = 5,                 -- the experience of all units is read every Nth pass (a pass is poll_ms)
        },
    },
    -- M04 bandits, iteration 01. First guesses from M00 decisions 11 to 15 and 28 to 30.
    bandits = {
        enabled = true,
        poll_ms = 1000,                  -- real time between two checks of Public Order
        start_order = 100,               -- mod order in a new game
        tick_days = 30,                  -- game days between two order ticks
        manor_term = 10,                 -- order gain for each tick (plus the tech tree order_bonus)
        homeless_term = 5,               -- order loss for each tick and each homeless family
        threshold = 25,                  -- order below this value starts the banditry timer
        timer_days = 90,                 -- game days from the timer start to the leave
        warn_days = 30,                  -- the warning banner shows when this many game days are left
        leavers = 18,                    -- families that leave when the timer expires
        order_gain = 25,                 -- order gain when the families leave
        min_families_left = 1,           -- the village never loses its last family to this feature
        buy_back = {                     -- iteration 03. Starting values, tuned in playtests.
            silver_per_family = 10,      -- 2 families cost 20 silver, the amount of the proven letter
            price_multiplier = 1.0,      -- tech nodes (M12): Iron Hand 1.25, Amnesty 0.5
            check_every = 5,             -- polls between two looks at a sent buy-back
            give_up_game_seconds = 120,  -- game time (not real time, the game may be paused) before a missing family counts as a failed deal
        },
    },
    -- change add-order-tooltip-rows: mod order rows in the Public Order tooltip
    order_tooltip = {
        enabled = true,
        poll_ms = 1000,   -- real time between two tries to set the hook (the tooltip class loads late)
        delay_ms = 60,    -- wait after updateContents (the game rebuilds the rows first)
    },
    -- M02 iteration 05: the raid widget (one menu for all raid information). Needs the pak InvasionMod_P.pak.
    raid_widget = {
        enabled = true,
        toggle_key = Key.F8,                 -- F7 is the policy menu of the other mod; change here if F8 clashes
        poll_ms = 100,                       -- real time between two looks at the click queue (clicks are hook events, spec 34)
        refresh_ms = 500,                    -- real time between two refreshes of the labels
        z_order = 500,
        position = { X = 300, Y = 150 },
    },
    -- add-scenario-settings-menu (#375): the menu that opens when a new game starts. The owner writes the background text.
    scenario_settings = {
        enabled = true,
        defaults = { yearly = 2, great = 2, vassal = 2, first_raid_years = 2, size_class = 2 }, -- levels Medium, 2 years, Medium size
        title = "The Hussites Are Coming",
        background_text = "Placeholder text. The owner writes the background of the scenario here: who the Hussites are, and why they ride against your village.",
        labels = { yearly = "Yearly player raid", great = "Great raid", vassal = "Vassal raids", first_raid_years = "First Hussite raid", size_class = "Raid size" },
        choice_names = {
            yearly = { "Off", "Easy", "Medium", "Hard" }, great = { "Off", "Easy", "Medium", "Hard" }, vassal = { "Off", "Easy", "Medium", "Hard" },
            first_raid_years = { "After 1 year", "After 2 years", "After 3 years" },
            size_class = { "Small", "Medium", "Large" },
        },
        vassals_warning = "Warning: vassals are not enabled.",
        begin_label = "Begin the game", defaults_label = "Use defaults",
        new_game_max_day = 10,               -- a game with no save file name is new only when its day is at most this (a fixture that lost savefileToLoad is not)
        intro_wait_s = 60,                   -- real seconds to wait for the intro cinematic to end before the menu opens anyway
        begin_speed = 1,                     -- the game speed after "Begin the game" (a new game starts at speed 0)
        disable_autosave = true,             -- send disable_autosave after the intro and after Begin (spike #358: the first call after a new game is undone)
        start_kit = { villagers = 10, silver = 300 }, -- given once at "Begin the game" of a new game (change add-scenario-start-kit, #425)
        poll_ms = 100,
        pause_guard_epsilon = 0.01,          -- game clock change between two looks that counts as "the game runs" while the menu is open (#418)
        z_order = 500, position = { X = 300, Y = 120 },
    },
    -- M06 sack_and_terms, iteration 01. All values are TBD for playtests (M00 gives only the range 20 to 50 percent).
    sack_and_terms = {
        enabled = true,
        sack = {
            share_min = 20,                  -- percent of buildings and families at difficulty 1 (M00)
            share_max = 50,                  -- percent at difficulty 3. Linear in between (decision 15), rounded up (decision 28).
            method = "collapse",             -- how buildings fall: "collapse" (ruin at once) or "fire" (burns; a fire may destroy part of the goods inside, accepted; villagers put the fire out unless enemy soldiers are near)
            min_families_left = 1,           -- a normal sack keeps this many families (spike S8: no people ends the game)
            lost_reasons = { "loot", "time" }, -- a role raid that leaves for one of these reasons won the battle (TBD rule)
            window_days = 360,               -- game days of the repeated-sack window, counted from its first sack
            limit = 2,                       -- the sack that brings the count in the window to this number is fatal
            fatal = { enabled = true },      -- a fatal sack removes every family and the game ends by itself
        },
        -- M06 iteration 02. Silver amounts are TBD (playtests).
        terms = {
            offer_on_spawn = true,           -- an offer opens when a lord raid spawns
            payment_base = 100,              -- one-time payment = payment_base x difficulty
            tribute_base = 30,               -- yearly tribute of a vassal = tribute_base x difficulty
            tribute_days = 360,              -- game days between two tributes
            poll_ms = 2000,                  -- real time between two looks at the tribute day
        },
    },
    -- M07 vassals. Values are TBD for playtests .
    vassals = {
        enabled = true,
        poll_ms = 2000,          -- real time between two checks of the goal
        goal = 2,                -- EGameGoals Endless (spec 26): a claim does not end the game
        max_vassals = 3,         -- M00: 2 or 3 vassals in the middle game
        lord_names = { "Aldric", "Bertram", "Conrad" }, -- names of the vassal lords, one for each slot
        scan_every = 3,          -- a region scan runs every Nth poll
        handover_attempts = 3,   -- failed handovers of one slot before the mod stops trying (a command retries)
        keep_peace = true,       -- declare peace again when a vassal lord is at war with the player (TBD: the lords started the war by themselves)
        growth_check_days = 10,  -- game days after the handover until the mod checks that the lord built
        growth_min_buildings = 3, -- fewer new buildings than this means the lord stalled (real runs: +10 or +0)
        -- Change add-vassal-sack-wipe. A Hussite sack collapses buildings until ruin_share of them are ruins, then all villagers are deleted.
        sack_wipe = {
            ruin_share = 0.80,       -- owner, 2026-10-20: the sack is complete at 80 percent ruins
            max_steps = 6,           -- sack steps (one for each vassal poll) before the mod gives up and logs an error
            free_stable_polls = 4,   -- polls with a stable family count of 0 before the slot is freed and the refugee wave starts
            retry_margin = 3,        -- buildings collapsed above the need in a retry step: the AI rebuilds ruins while the sack runs
            max_wiped = 6,           -- wiped regions that the mod remembers for a restore
            -- Owner, 2026-10-22: a sack removes all logs and planks of the region. A sack that ends without a wipe gives some back and orders the rebuild at once.
            wood = { { id = 16, name = "logs" }, { id = 17, name = "planks" } },
            give = { { id = 16, amount = 50, name = "logs" }, { id = 17, amount = 100, name = "planks" } },
            deposit_tries = 10,      -- buildings tried for each good
        },
        -- Restore of a wiped village (owner, 2026-10-21): flat silver, 5 families, and goods so that the AI starts to rebuild.
        restore = {
            silver = 100,
            goods = { { id = 16, amount = 100, name = "logs" }, { id = 17, amount = 200, name = "planks" }, { id = 15, amount = 100, name = "rubble_stone" } },
            deposit_tries = 10,      -- buildings tried for each good
            rebuilt_share = 0.50,    -- the village is rebuilt when this share of the ruins that the restore ordered is built (a site does not count); then the tribute starts (TBD)
        },
        -- Iteration 03. Policies are mod-owned. Values are TBD for playtests.
        policies = {
            light = { tribute = 0.5 },   -- tribute factor on the M08 share
            fair = { tribute = 1.0 },
            heavy = { tribute = 1.5 },
        },
    },
    -- M10 finite_resources. Home deposits are a mod-owned stock. Values are TBD for playtests (M00: last 2 to 4 game years at normal use).
    finite_resources = {
        enabled = true,
        poll_ms = 5000,            -- real time between two looks at the production of the buildings
        window_days = 36500,       -- getGoodsProducedOver window: the whole life of a building
        resources = {
            iron = { good = 14, size = 400 }, -- EItemType IronOre; units that the iron mines may still produce
            salt = { good = 145, size = 300 }, -- EItemType Salt (M10.02, TBD)
            clay = { good = 146, size = 500 }, -- EItemType Clay (M10.02, TBD)
        },
    },
    -- M08 tribute. Values are TBD for playtests (M00: 10 to 30 percent of the production).
    tribute = {
        enabled = true,
        poll_ms = 2000,           -- real time between two looks at the season
        units_per_family = 20,    -- production units of one family in one season (TBD)
        share = 0.20,             -- share of the production that a vassal sends (fixed; decision of 2026-10-20: no vassal loyalty)
        siege = { days = 8, min_living = 0.5, poll_ms = 2000 }, -- M02.07: a subjugation raid on a vassal takes it after days with min_living share of units (TBD)
        goods = { { id = 30, name = "fish" }, { id = 16, name = "timber" } }, -- the tribute is split equally
        -- M10.02: the permanent supply of the goods that run out at home. Paid next to `goods`, with the same share. Values are TBD.
        finite_goods = { { id = 14, name = "iron", units_per_family = 10 }, { id = 145, name = "salt", units_per_family = 6 } },
    },
    -- liege_influence (change add-liege-influence). Values are owner decisions of 2026-10-19 and 2026-10-20.
    -- Influence changes only by contracts (liege_contracts). The liege window values (poll, refresh, z_order, position) are used by that feature.
    liege_influence = {
        enabled = true,
        -- Arms shipment (change add-scenario-start-kit, #425): the button "Request arms shipment" of the liege screen.
        arms_shipment = {
            cost = 200,                  -- silver
            cooldown_days = 180,         -- game days between two shipments
            goods = { { id = 271, amount = 30, name = "large shield" }, { id = 133, amount = 30, name = "spear" } }, -- item ids from DT_Items (notes/item-ids.md)
        },
        poll_ms = 100,                   -- real time between two looks at the click queue of the menu (never faster)
        refresh_ms = 500,                -- real time between two refreshes of the menu labels
        z_order = 500,
        position = { X = 50, Y = 25 },   -- the contracts window is wide: it starts near the top left corner
    },
    -- liege_contracts (change update-liege-tribute-to-contracts, #505). The contracts themselves are in data/liege_contracts/contracts.json.
    liege_contracts = {
        enabled = true,
        poll_ms = 2000,       -- real time between two looks at the season, the progress and the deadline
        fail_penalty = 500,   -- influence taken when a contract is not complete at its deadline (never below 0); the same for all contracts
        data_file = "data/liege_contracts/contracts.json", -- relative to the mod folder
        spring_season = 1,    -- TemporalComponent.Season values (notes/season-values.md): winter 0, spring 1, summer 2, autumn 3
        winter_season = 0,
    },
    -- M13 manor_stronghold. Values are TBD for playtests.
    manor_stronghold = {
        enabled = true,
        storage_base_capacity = 200,  -- units of goods in one manor module (spec 12)
        -- M13.03: extra retinue squads above the native limit of 12 men (made with spawnArmy, paid by the mod). TBD.
        squad_template = "retinue_tier1",
        squad_men = 36,               -- men in one squad (measured, run 20261018-141330-93b7)
        bonus_per_squad = 12,         -- retinue bonus (tech tree) needed for each extra squad
    },
    -- M12 tech_tree. The node data is in data/tech_tree/tree.json. Values are TBD for playtests.
    tech_tree = {
        enabled = true,
        poll_ms = 2000,              -- real time between two looks at the settlement level and the garrison
        max_active_laws = 2,         -- M12.04: laws in force at the same time (TBD)
        slots_per_level = 1,         -- decision 24: one node slot for each settlement level
        tree_file = "data/tech_tree/tree.json", -- relative to the mod folder
    },
    -- M12 iteration 02: the tech tree menu. Needs the pak InvasionMod_P.pak.
    tech_tree_widget = {
        enabled = true,
        toggle_key = Key.F9,                 -- F7 is the policy menu and F8 the raid menu
        poll_ms = 100,                       -- real time between two looks at the click queue (clicks are hook events, spec 34)
        refresh_ms = 500,                    -- real time between two refreshes of the labels
        z_order = 500,
        position = { X = 300, Y = 150 },
        step_x = 180, step_y = 60,           -- pixels for one layout unit of a node
    },
    -- M09 refugees. Values are TBD for playtests (owner, 2026-10-20: 50 percent of the vassal population).
    refugees = {
        enabled = true,
        share_min = 0.50,         -- share of the vassal families that flee (owner, 2026-10-20: 50 percent)
        share_max = 0.50,
        families_per_call = 5,    -- one settleRegion call adds 5 families (spec 15)
        max_calls = 3,            -- most calls in one wave
        timeout_days = 45,        -- game days until unhoused refugees turn to bandits (M00: 1 to 2 game months; TBD)
        poll_ms = 4000,           -- real time between two looks at an active wave
        max_rebel_families = 6,   -- most families that turn in one go (homeless_rebel limit)
        families_per_squad = 2,   -- as in bandits
    },
}
