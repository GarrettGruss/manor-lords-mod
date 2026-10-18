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
    },
}
