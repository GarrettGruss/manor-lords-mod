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
        difficulty = 1,                                      -- start value, 1 to 3. The player picks it (start UI comes later).
        first_raid_days_min = 30, first_raid_days_max = 90,  -- game days from the day the plan is made
        warning_days_min = 14, warning_days_max = 56,        -- 2 to 8 game weeks
        size_multipliers = { small = 1, medium = 2, large = 3 }, -- squads = multiplier x difficulty
        squad_units = 18,                                    -- units in one squad of spawnRaiders
        base_timer_floor = 300,                              -- the mod lifts the base game raid timer when it falls under this
        base_timer_refill = 700,
        great_raid = {                                       -- M02 iteration 02: the clock to the great raid (365 game days a year)
            min_days = 3 * 365, max_days = 5 * 365,          -- M00 balance target: 3 to 5 game years
            banner_every_days = 30,
            relief_full_squads = 15,                         -- relief army at difficulty 1 (decisions 17, 26)
            wave_squads = 15,                                -- a large army (decision 16)
            -- M02 iteration 06: the waves, the relief army and the final battle. All values are TBD for playtests.
            wave_gap_days = 10,                              -- game days between two waves
            relief_delay_days = 10,                          -- game days from the last wave to the relief army and the final battle
            final_squads = 25,                               -- "very large" (more than the 15 of a large army); not scaled by difficulty
            final_tier_difficulty = 2,                       -- the tier mix of the final army (roles table of this difficulty)
            relief_templates = { "militiaFoot", "spearMilitia", "bowMilitia", "crossbowMilitia" }, -- the liege squads, cycled
            relief_offset = { x = 0, y = 2500 },             -- the relief army appears this far from the player pawn
            prompt_every_days = 7,                           -- iteration 04: the pick prompt repeats until the player picks                          -- a banner for the clock when no minor raid banner shows
        },
        -- M02 iteration 03: the subjugation raid (major). One is planned after the first raid. Values are TBD for playtests.
        subjugation = {
            enabled = true,
            wait_days_min = 60, wait_days_max = 120,         -- game days from the first raid spawn to the subjugation raid
            size_class = 3,                                  -- large: squads = 3 x difficulty (TBD, "major" has no size rule in M00)
        },
        poll_ms = 300,                                       -- real time between two checks of the game day
        seed = nil,                                          -- nil: seed from the clock
        -- M05 iteration 02: Hussite roles of a raid (decision 7). All weights and shares are TBD for playtests.
        -- Templates are rows of DT_UnitTemplates, checked in the real game (docs/mod/M05-unit_balance/iterations/02-hussite-roles.md).
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
    -- M03 raid_behavior, iteration 01. The native plunder AI is left alone.
    raid_behavior = {
        enabled = true,
        poll_ms = 1000,         -- real time between two looks at the raiders
        slow_every = 5,         -- the building scan and the AI log scan run every Nth look (they read many objects)
        carry_cap = 10,         -- most loot (ItemsLooted) one raider keeps. Hussite grain 10 (M00). The native AI reaches 4 or 5.
        exit_y = -85000,        -- a raider that vanishes at or below this y walked off the map. It keeps its loot.
        fallback_good = 16,     -- good type for loot when the nearest store has no goods
        -- M03 iteration 02: a role raid (spawnArmy squads) leaves like a native raid. All values are TBD for playtests.
        plunder = {                 -- the plunder tick of a lord raid: goods leave the stores while the army stands at the manor
            battle_radius = 4000,   -- a raider counts as inside this far from the manor (the army stood within 1300 in run 20261018-035856-248b)
            per_unit_day = 1,       -- goods taken for each raider inside, each game day. The goal is leave.loot_per_raider for each raider.
        },
        leave = {
            enabled = true,
            loot_per_raider = 4,    -- leaves when the loot taken is this much for each raider of the start (native raiders carry 4 to 5)
            loss_share = 0.5,       -- leaves when this share of the raiders died
            quiet_distance = 40000, -- a leaving raider is removed only this far from the player pawn (or at exit_y). User decision: no deletion in view.
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
    },
    -- M04 bandits, iteration 01. First guesses from M00 decisions 11 to 15 and 28 to 30.
    bandits = {
        enabled = true,
        poll_ms = 1000,                  -- real time between two checks of Public Order
        bands = {                        -- the chance applies when Public Order is below "below"; the lowest matching band wins
            { below = 75, chance = 0.10 },
            { below = 50, chance = 0.25 },
            { below = 25, chance = 0.50 },
        },
        families_per_conversion = 2,     -- families removed by one successful roll
        families_per_squad = 2,          -- one Brigands squad (18 units) per 2 families (spike 15 proposal)
        min_families_left = 1,           -- the village never loses its last family to this feature
        buy_back = {                     -- iteration 03. Starting values, tuned in playtests.
            silver_per_family = 10,      -- 2 families cost 20 silver, the amount of the proven letter
            price_multiplier = 1.0,      -- tech nodes (M12): Iron Hand 1.25, Amnesty 0.5
            check_every = 5,             -- polls between two looks at a sent buy-back
            give_up_game_seconds = 120,  -- game time (not real time, the game may be paused) before a missing family counts as a failed deal
        },
    },
    -- M02 iteration 05: the raid widget (one menu for all raid information). Needs the pak raidmenu_P.pak.
    raid_widget = {
        enabled = true,
        toggle_key = Key.F8,                 -- F7 is the policy menu of the other mod; change here if F8 clashes
        poll_ms = 200,                       -- real time between two checks of the buttons and the texts
        click_cooldown_s = 0.4,
        z_order = 500,
        position = { X = 300, Y = 150 },
    },
    -- M06 sack_and_terms, iteration 01. All values are TBD for playtests (M00 gives only the range 20 to 50 percent).
    sack_and_terms = {
        enabled = true,
        sack = {
            share_min = 20,                  -- percent of buildings, stock and families at difficulty 1 (M00)
            share_max = 50,                  -- percent at difficulty 3. Linear in between (decision 15), rounded up (decision 28).
            method = "collapse",             -- how buildings fall: "collapse" (ruin at once) or "fire" (burns, goods inside are lost)
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
    -- M07 vassals. Values are TBD for playtests (M00 gives no loyalty numbers).
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
        loyalty_start = 50,      -- loyalty of a new vassal, 0 to 100
    },
    -- M08 tribute. Values are TBD for playtests (M00: 10 to 30 percent of the production).
    tribute = {
        enabled = true,
        poll_ms = 2000,           -- real time between two looks at the season
        units_per_family = 20,    -- production units of one family in one season (TBD)
        share_min = 0.10,         -- share of the production at loyalty 0
        share_max = 0.30,         -- share of the production at loyalty 100
        goods = { { id = 30, name = "fish" }, { id = 16, name = "timber" } }, -- the tribute is split equally (M10 adds iron and salt)
    },
    -- M12 tech_tree. The node data is in data/tech_tree/tree.json. Values are TBD for playtests.
    tech_tree = {
        enabled = true,
        poll_ms = 2000,              -- real time between two looks at the settlement level and the garrison
        slots_per_level = 1,         -- decision 24: one node slot for each settlement level
        tree_file = "data/tech_tree/tree.json", -- relative to the mod folder
    },
}
