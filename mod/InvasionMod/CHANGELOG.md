# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Feature `bandits` (M04.03, #167): coin buy-back. Command `bandits_buy_back` refuses when silver is short, no home is free, or no family is outstanding; otherwise it sends the settle letter with the price. A failed deal (no family in 120 game seconds) is refunded. New config `bandits.buy_back` (`silver_per_family`, `price_multiplier`). State shows `outstanding_families`, `returned_families`, `free_slots`, `silver`, `buy_backs`.
- Feature `bandits` (M04.02, #161): one conversion roll per season change (saved last season, no repeat after a load). The config key `tick_days` is removed. State command shows `season` and `last_season`.
- Mod M05.01 (#156): feature `unit_balance` of `InvasionMod`. A poll cuts `def` and `block` of unarmored units (def below 10) to 0, for all sides. Commands `unit_balance_state`, `unit_balance_set`, `unit_balance_apply`; scenarios `unit-balance-lethality`, `unit-balance-armored-kept`; suite `unit-balance-ab`. Real game: militia loss rate x2.14 (p 0.058). Notes `docs/mod/M05-unit_balance/implementation-notes/iteration-01-unarmored-lethality.md`.
- Feature `bandits` (M04.01, #155): low approval lowers Public Order (debuff = ceil((100 - approval) x difficulty), written again after each game rewrite), and low Public Order turns families into bandits through `homeless_rebel` (fixed 30 day tick, bands 10, 25 and 50 percent). Commands `bandits_state`, `bandits_set_approval`, `bandits_tick_now`.
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
