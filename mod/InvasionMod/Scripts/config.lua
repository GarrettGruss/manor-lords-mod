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
    -- M02 invasion, iteration 01. First guesses from the M00 balance targets.
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
    },
    -- M03 raid_behavior, iteration 01. The native plunder AI is left alone.
    raid_behavior = {
        enabled = true,
        poll_ms = 1000,         -- real time between two looks at the raiders
        carry_cap = 10,         -- most loot (ItemsLooted) one raider keeps. Hussite grain 10 (M00). The native AI reaches 4 or 5.
        exit_y = -85000,        -- a raider that vanishes at or below this y walked off the map. It keeps its loot.
        fallback_good = 16,     -- good type for loot when the nearest store has no goods
    },
}
