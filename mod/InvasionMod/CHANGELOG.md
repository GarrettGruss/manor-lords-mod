# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
