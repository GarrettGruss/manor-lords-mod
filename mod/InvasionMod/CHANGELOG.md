# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Feature `raid_behavior` (M03.02, #168): a role raid (spawnArmy squads) leaves after enough loot, enough losses or a time limit. The loot is counted as carried out. Config `raid_behavior.leave`. The state command shows `roles` and `leave_reason`.
- Hussite roles (M05.02, #162): the raid plan stores `composition_seed`; the raid spawns one squad for each planned template through `spawnArmy` (config `invasion.roles`). Commands `invasion_set_roles`, `invasion_raid_squads`. `invasion_state` reports `composition` and the unit count of the composition.
- Feature `bandits` (M04.02, #161): one conversion roll per season change (saved last season, no repeat after a load). The config key `tick_days` is removed. State command shows `season` and `last_season`.
- Mod M05.01 (#156): feature `unit_balance` of `InvasionMod`. A poll cuts `def` and `block` of unarmored units (def below 10) to 0, for all sides. Commands `unit_balance_state`, `unit_balance_set`, `unit_balance_apply`; scenarios `unit-balance-lethality`, `unit-balance-armored-kept`; suite `unit-balance-ab`. Real game: militia loss rate x2.14 (p 0.058). Notes `docs/mod/M05-unit_balance/implementation-notes/iteration-01-unarmored-lethality.md`.
- Feature `bandits` (M04.01, #155): low approval lowers Public Order (debuff = ceil((100 - approval) x difficulty), written again after each game rewrite), and low Public Order turns families into bandits through `homeless_rebel` (fixed 30 day tick, bands 10, 25 and 50 percent). Commands `bandits_state`, `bandits_set_approval`, `bandits_tick_now`.
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
