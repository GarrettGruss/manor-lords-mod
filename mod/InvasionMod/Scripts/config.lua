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
}
