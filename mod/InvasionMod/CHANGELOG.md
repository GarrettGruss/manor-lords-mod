# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Added
- Mod M07.01 (#187): feature `vassals` of `InvasionMod`. The mod writes goals = Endless on every start and load (a claim no longer ends the game) and keeps a 3 slot vassal registry with loyalty in ModState. Commands `vassals_state`, `vassals_claim`, `vassals_set_loyalty`, `vassals_set_goal`. Scenario `vassals-claim-without-victory`.
- Feature `invasion` (M02.06, #186): great raid phases (`gr_*` ModState keys), `great_raid.next_action`, `relief.lua`, config `invasion.great_raid` wave and final values, three `invasion_great_*` commands. `raid_behavior` exports `final_raid_ended`; a `great` raid has no plunder and no leave.
### Fixed
- Feature `raid_behavior`: a non-number `ItemsLooted` no longer raises an error in the unit scan.
- Feature `invasion` (M02.03, #177): subjugation raid with its own ModState keys (`sub_*`), `target.lua`, config `invasion.subjugation`. `raid_behavior`: no plunder and no leave for a subjugation raid; the tracker shows `kind`.
- Feature `sack_and_terms` (M06.02, #181): terms. Commands `terms_state`, `terms_offer`, `terms_accept` (payment or vassalage), `terms_decline`. `raid_behavior` exports `force_leave` and `active_role_raid`. Config `sack_and_terms.terms`.
- Feature `raid_behavior` (M03.02 follow-up, #172): test commands `raid_behavior_test_set_leave`, `raid_behavior_test_take_region`, `raid_behavior_test_kill_raiders` (session only). Feature `invasion`: a lord raid that fails after a partial spawn adds no bandit squads.
- Feature `sack_and_terms` (M06.01, #173): sack after a lost battle (config `sack_and_terms.sack`). `raid_behavior` gains `watch_leave`. Commands `sack_state`, `sack_now`, `sack_set_fatal`. `HarnessSack` is a shared module of the mod.
- Feature `invasion` (M02.04, #175): difficulty pick command and prompt banner, ModState keys `difficulty_chosen`, `last_prompt_day`, rules in `difficulty.lua`. Commands `invasion_pick_difficulty`, `invasion_difficulty_state`.
- Feature `invasion` (M02.02, #171): great raid clock of 3 to 5 game years in ModState (`great_raid_day`, `last_clock_banner_day`), shown in the second banner line and in a banner every 30 days. Commands `invasion_clock_state`, `invasion_clock_set_days_left`. Config `invasion.great_raid`.
- Feature `raid_behavior` (M03.02, #168): a Hussite role raid is a lord army anchored at the manor (`features/invasion/lord_raid.lua`, config `invasion.roles.lord_army`) with a plunder tick; it leaves by peace after enough loot, losses or time. Fallback squads are removed only in a quiet spot. Config `raid_behavior.leave`. The state command shows `roles` and `leave_reason`.
- Feature `bandits` (M04.03, #167): coin buy-back. Command `bandits_buy_back` refuses when silver is short, no home is free, or no family is outstanding; otherwise it sends the settle letter with the price. A failed deal (no family in 120 game seconds) is refunded. New config `bandits.buy_back` (`silver_per_family`, `price_multiplier`). State shows `outstanding_families`, `returned_families`, `free_slots`, `silver`, `buy_backs`.
- Hussite roles (M05.02, #162): the raid plan stores `composition_seed`; the raid spawns one squad for each planned template through `spawnArmy` (config `invasion.roles`). Commands `invasion_set_roles`, `invasion_raid_squads`. `invasion_state` reports `composition` and the unit count of the composition.
- Feature `bandits` (M04.02, #161): one conversion roll per season change (saved last season, no repeat after a load). The config key `tick_days` is removed. State command shows `season` and `last_season`.
- Mod M05.01 (#156): feature `unit_balance` of `InvasionMod`. A poll cuts `def` and `block` of unarmored units (def below 10) to 0, for all sides. Commands `unit_balance_state`, `unit_balance_set`, `unit_balance_apply`; scenarios `unit-balance-lethality`, `unit-balance-armored-kept`; suite `unit-balance-ab`. Real game: militia loss rate x2.14 (p 0.058). Notes `docs/mod/M05-unit_balance/implementation-notes/iteration-01-unarmored-lethality.md`.
- Feature `bandits` (M04.01, #155): low approval lowers Public Order (debuff = ceil((100 - approval) x difficulty), written again after each game rewrite), and low Public Order turns families into bandits through `homeless_rebel` (fixed 30 day tick, bands 10, 25 and 50 percent). Commands `bandits_state`, `bandits_set_approval`, `bandits_tick_now`.
- Feature `raid_behavior` (M03.01, #144): raid tracker, carry cap, loot of a dead raider back to the nearest store. Command `raid_behavior_state`. The `invasion` feature gets `watch_spawn` for other features.
- Feature `invasion` (M02.01, #143): one scheduled minor raid, daily countdown banner, base raid timer kept high. Commands `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`.

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
