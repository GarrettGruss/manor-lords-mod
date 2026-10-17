# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Mod M05.01 (#156): feature `unit_balance` of `InvasionMod`. A poll cuts `def` and `block` of unarmored units (def below 10) to 0, for all sides. Commands `unit_balance_state`, `unit_balance_set`, `unit_balance_apply`; scenarios `unit-balance-lethality`, `unit-balance-armored-kept`; suite `unit-balance-ab`. Real game: militia loss rate x2.14 (p 0.058). Notes `docs/mod/M05-unit_balance/implementation-notes/iteration-01-unarmored-lethality.md`.
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
