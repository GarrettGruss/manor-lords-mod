# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Feature `bandits` (M04.01, #155): low approval lowers Public Order (debuff = ceil((100 - approval) x difficulty), written again after each game rewrite), and low Public Order turns families into bandits through `homeless_rebel` (fixed 30 day tick, bands 10, 25 and 50 percent). Commands `bandits_state`, `bandits_set_approval`, `bandits_tick_now`.
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
