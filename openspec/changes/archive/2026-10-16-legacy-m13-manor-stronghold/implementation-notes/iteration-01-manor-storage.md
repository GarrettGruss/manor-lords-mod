# Iteration 01: manor storage

- The capacity is a mod rule. `HarnessManor.manor_put` refuses a put above `HarnessManor.CAPACITY`. The feature `manor_stronghold` sets that field to `storage_base_capacity + bonus`. No row write of `buildingStats` was needed, so open question 16 of M00 (row write plus instance copy) is not needed for the mod store.
- The bonus is the tech tree effect kind `manor_storage` (add). `tech_tree` pushes the total to `manor_stronghold.set_modifiers` with the other effects.
- The capacity is per manor module. A village with one built module has 200, then 400 after one upgrade node.
- Real game: fixture `manor-bailey` has a built manor house (type 98) with the region manor set, so no mouse is needed. The base fill of the module is read first, so the scenario does not assume an empty module.
- Not done: the base game does not carry goods into the manor by itself. Players use the commands. A UI for put and take is not planned.
