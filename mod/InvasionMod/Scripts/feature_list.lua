-- The features of this mod and what each one needs. Keep it equal to "features" in mod.json.
-- A test compares the two lists.
return {
    { name = "example", requires = {} },
    { name = "mod_state", requires = {} },
    { name = "invasion", requires = { "mod_state" } },
    { name = "raid_behavior", requires = { "invasion" } },
    { name = "unit_balance", requires = {} },
    { name = "bandits", requires = { "invasion" } },
    { name = "sack_and_terms", requires = { "raid_behavior", "vassals" } },
    { name = "vassals", requires = { "mod_state" } },
    { name = "tribute", requires = { "vassals", "raid_behavior" } },
    { name = "raid_widget", requires = { "invasion" } },
    { name = "scenario_settings", requires = { "invasion" } },
    { name = "manor_stronghold", requires = {} },
    { name = "finite_resources", requires = { "mod_state" } },
    { name = "tech_tree", requires = { "bandits", "unit_balance", "mod_state", "manor_stronghold", "vassals", "tribute" } },
    { name = "refugees", requires = { "vassals", "bandits" } },
    { name = "tech_tree_widget", requires = { "tech_tree" } },
    { name = "liege_influence", requires = { "mod_state", "tribute" } },
}
