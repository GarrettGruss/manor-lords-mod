-- The features of this mod and what each one needs. Keep it equal to "features" in mod.json.
-- A test compares the two lists.
return {
    { name = "example", requires = {} },
    { name = "mod_state", requires = {} },
    { name = "invasion", requires = { "mod_state" } },
    { name = "raid_behavior", requires = { "invasion" } },
    { name = "unit_balance", requires = {} },
    { name = "bandits", requires = { "invasion" } },
    { name = "sack_and_terms", requires = { "raid_behavior" } },
    { name = "raid_widget", requires = { "invasion" } },
    { name = "vassals", requires = { "mod_state" } },
}
