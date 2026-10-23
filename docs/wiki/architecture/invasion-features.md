---
type: Reference
title: Invasion Mod features
description: The features of mod/InvasionMod - what each one implements now, its named commands, its dependencies on other features, and its mod spec.
tags: [invasion-mod, features, commands, dependencies]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T16:15:30Z }
sources:
  - resource: repo://mod/InvasionMod/Scripts/features/
  - resource: repo://mod/InvasionMod/Scripts/feature_list.lua
  - resource: repo://mod/InvasionMod/Scripts/config.lua
  - resource: repo://mod/InvasionMod/scenarios/
  - resource: repo://design/mod/README.md
  - resource: repo://openspec/changes/archive/2026-10-16-legacy-mod-feature-breakdown/README.md
  - resource: repo://openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/implementation-notes/f9-key-crash.md
---
# Invasion Mod features

The mod loads features in dependency order. See [Invasion Mod structure](invasion-mod.md) for the loader, the scheduler and the config. This page says what each feature does now. It does not add design. The design is in [`design/`](../../../design/mod/invasion-mod.md), which the user writes. Mod doc rules: [`design/mod/README.md`](../../../design/mod/README.md).

Every command name starts with `InvasionMod.`. The tables omit that prefix. Commands are registered with `HarnessCommands`. The harness and the agent call them. Mods and scenarios do not use eval. Most features have a `*_state` command that returns the current values.

## Dependency graph

```mermaid
flowchart LR
  mod_state --> invasion
  mod_state --> vassals
  mod_state --> finite_resources
  invasion --> raid_behavior
  invasion --> bandits
  invasion --> raid_widget
  raid_behavior --> sack_and_terms
  vassals --> sack_and_terms
  vassals --> tribute
  raid_behavior --> tribute
  vassals --> refugees
  bandits --> refugees
  bandits --> tech_tree
  unit_balance --> tech_tree
  mod_state --> tech_tree
  manor_stronghold --> tech_tree
  vassals --> tech_tree
  tribute --> tech_tree
  tech_tree --> tech_tree_widget
```

An arrow means "is required by". `example`, `unit_balance` and `manor_stronghold` have no requirements. The source of truth is `feature_list.lua`, which must equal `mod.json`.

## Summary

| Feature | Spec | Requires | Scenarios |
| --- | --- | --- | --- |
| example | none (layout stub) | none | none |
| mod_state | [M01](../../../openspec/changes/archive/2026-10-16-legacy-m01-mod-state/README.md) | none | `scenarios/mod_state/` |
| invasion | [M02](../../../openspec/changes/archive/2026-10-16-legacy-m02-invasion/README.md) | mod_state | `scenarios/invasion/` |
| raid_widget | [M02](../../../openspec/changes/archive/2026-10-16-legacy-m02-invasion/README.md) (iteration 05) | invasion | `scenarios/invasion/raid_widget.py` |
| scenario_settings | change `add-scenario-settings-menu` (#375) | invasion | `scenarios/scenario_settings/` |
| raid_behavior | [M03](../../../openspec/changes/archive/2026-10-16-legacy-m03-raid-behavior/README.md) | invasion | `scenarios/raid_behavior/` |
| bandits | [M04](../../../openspec/changes/archive/2026-10-16-legacy-m04-bandits/README.md) | invasion | `scenarios/bandits/` |
| unit_balance | [M05](../../../openspec/changes/archive/2026-10-16-legacy-m05-unit-balance/README.md) | none | `scenarios/unit_balance/` |
| sack_and_terms | [M06](../../../openspec/changes/archive/2026-10-16-legacy-m06-sack-and-terms/README.md) | raid_behavior, vassals | `scenarios/sack_and_terms/` |
| vassals | [M07](../../../openspec/changes/archive/2026-10-16-legacy-m07-vassals/README.md) | mod_state | `scenarios/vassals/` |
| tribute | [M08](../../../openspec/changes/archive/2026-10-16-legacy-m08-tribute/README.md) | vassals, raid_behavior | `scenarios/tribute/` |
| refugees | [M09](../../../openspec/changes/archive/2026-10-16-legacy-m09-refugees/README.md) | vassals, bandits | `scenarios/refugees/` |
| finite_resources | [M10](../../../openspec/changes/archive/2026-10-16-legacy-m10-finite-resources/README.md) | mod_state | `scenarios/finite_resources/` |
| tech_tree | [M12](../../../openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/README.md) | bandits, unit_balance, mod_state, manor_stronghold, vassals, tribute | `scenarios/tech_tree/` |
| tech_tree_widget | [M12](../../../openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/README.md) (iteration 02) | tech_tree | `scenarios/tech_tree/widget.py`, `widget_laws.py`, `widget_key.py` |
| manor_stronghold | [M13](../../../openspec/changes/archive/2026-10-16-legacy-m13-manor-stronghold/README.md) | none | `scenarios/manor_stronghold/` |

The feature `liege_influence` (change `add-liege-influence`, #271, replaces the old M11 spec) needs `mod_state` and `tribute`. The player pays silver from the lord treasury as tribute (commands `liege_state`, `liege_send_tribute`, or the pak widget `WBP_LiegeTribute`, opened by the Liege button in the bottom bar) and gets influence: 10 silver for 1 influence, no decay, no cap. Test scenarios: `scenarios/liege_influence/`.

Specs without code: [M14 plundered_start](../../../openspec/changes/archive/2026-10-16-legacy-m14-plundered-start/README.md) is out of scope for the first release. M14 has no feature folder.

## Features

### example
A stub. It shows the layout and proves that a feature module loads. It does nothing else. Its row patches (`data/example/patches/`) test the pak build.

### mod_state (M01)
Keeps the values of the mod inside the save through the shared module `ModState`. Other features call `ModState.open("invasion", "pawn", version)` and `register(key, default, kind)`. The state is stored in the player pawn `Tags` in Lua, never through the bridge `set`. `config.mod_state.keys` registers the `selftest_*` keys for the M01 scenarios.
Commands: `mod_state_dump`, `mod_state_get`, `mod_state_set`, `mod_state_add_foreign_tag`.

### invasion (M02)
The mod owns the raid timer. Files: `plan.lua`, `difficulty.lua`, `great_raid.lua`, `target.lua`, `relief.lua`, `lord_raid.lua`, `init.lua`. The plan lives in ModState, so it survives a load. A scheduler job polls the game day (`poll_ms`).
- Raid clock (change `update-raid-clock-yearly`): no raid in game year 1. From year 2 one raid a year. At each season change `yearly_step` rolls once (`config.invasion.yearly.chance_by_season`, default 25, 33, 50, 100 percent; the fourth season always raids). The pure rules are `plan.season_year`, `plan.should_raid` and `plan.yearly_raid`. A season change is counted in ModState (`yearly_season_no`, `yearly_last_season`, `yearly_done_year`), saved before the roll like in `mod/bandits`, so a load does not roll again. Year 1 is the first 4 seasons after the mod started. A successful roll plans a raid 1 to `season_days` (90) game days ahead. Kind rules: the first yearly raid is plunder, the second is the subjugation raid (once), later raids are plunder again (`plunder_spawned`, `sub_spawned`).
- Banners (change `update-raid-banners`): a yearly raid has no banner, except a large plunder raid (the player raid). A subjugation raid and a large plunder raid show one banner, `config.invasion.raid_banner_days` (30) game days before the raid day (or on the plan day), with the target (`you` or `your vassal <name>`) and the size estimate. The flags `plunder_banner` and `sub_banner` in ModState stop a repeat after a load. The vassal of a subjugation raid comes from the saved `sub_seed`, so the banner and the spawn name the same one. There is no difficulty banner (the settings menu owns the difficulty). The raid spawns on the planned day, with squads scaled by size class and difficulty.
- The great raid clock, its waves, the relief army and the final battle (iterations 02 and 06). The clock ends at the first day of game year `great_raid.start_year` (default 10; the year is the count of season changes of the yearly rule, 4 a year). `great_raid_day` is an estimate (92 days a season) until that year begins, then it is set to the real day. One clock banner (`Great raid in N years`) shows at the start of each of the 3 years before: only when the year changed in this Lua session, so a load skips a missed one, and `last_clock_banner_year` stops a repeat. None when great raids are off.
- Difficulty 1 to 3, picked by the player (iteration 04). Raid squads use Hussite roles (`config.invasion.roles`): melee and ranged tiers from game unit templates. With `lord_army` the raid is the army of an AI lord at war with the player, else bandit squads.
- Vassals can be targets (iteration 07, `target.lua`).
- Corpse pit loot (change `add-corpse-pit-loot`): `raid_behavior` records the goods of each plunder tick per Hussite raid (`raid.plunder_goods`, text key `raid_plunder_record`). `pit_poll` (each `pit_poll_ms`) reads the corpse count (`Type 233`) of the pit (building 113); each rise pays one share (`floor(record / initial)`) for each unpaid dead Hussite raider (`rules.pay_bodies`) with `addToInventory`. No hook exists for a delivery. Native raids, unknown bodies and a missing pit give nothing. Test command `raid_behavior_pit_state`.

Commands: `invasion_state`, `invasion_force_next`, `invasion_set_difficulty`, `invasion_set_size`, `invasion_set_roles`, `invasion_raid_squads`, `invasion_difficulty_state`, `invasion_pick_difficulty`, `invasion_clock_state`, `invasion_clock_set_days_left`, `invasion_great_state`, `invasion_great_force_start`, `invasion_great_skip_wait`, `invasion_subjugation_state`, `invasion_subjugation_force_next`, `invasion_yearly_state`, `invasion_yearly_advance_season` (test: counts one season change and rolls, optional fixed `roll`), `invasion_plan_now` (test: plans a raid now, optional `kind`). `invasion_force_next` plans a plunder raid first when none is planned.

### raid_widget (M02 iteration 05)
One menu for all raid information. The layout is a cooked Widget Blueprint in `raidmenu_P.pak` (`ue/make_raid_widget.py`): a title, text lines and three unused Borders (the old difficulty buttons). Lua fills the texts (`lines.lua`). The menu is built on the base menu ([Base menu](#base-menu)): a Raid button in the game's bottom bar opens it with one click. F8 stays as a shortcut (`config.raid_widget.toggle_key`); the key only sets a flag, the base menu tick toggles (see [Shared patterns](#shared-patterns)). The menu has no difficulty buttons (removed by change `add-scenario-settings-menu`): the player picks the difficulty in the scenario settings menu. Since change `update-raid-banners` the lines are: yearly raid, subjugation raid (type, target, size, days left; each shows "not planned yet" when no raid is planned), great raid, difficulty, terms. A switched-off raid type (subjugation off, great raids off) has an empty line. The old text: the line "Great raid" showed "off" when Great raids is Off.
Commands: `raid_widget_open`, `raid_widget_close`, `raid_widget_state`.

### scenario_settings (change `add-scenario-settings-menu`, #375)
The menu that opens when a new game starts: a title, a background text, four rows (Difficulty, First Hussite raid, Raid size, Great raids) and the buttons "Use defaults" and "Begin the game". Built on the base menu ([Base menu](#base-menu)) with `bar = false` (no bottom bar button). The layout is the cooked Widget Blueprint `WBP_ScenarioSettings` in `raidmenu_P.pak` (`ue/make_scenario_settings_widget.py`; click buttons are `WBP_ClickButton`). Texts, defaults and limits are in `config.scenario_settings`; the background text is a placeholder until the owner writes it.
- **New game or loaded save** (`rules.kind_of_game`, decided once per session when the mod state is loaded): `settings_applied` = 1 means loaded. An empty `MLGameInstance.savefileToLoad` and a game day of at most `new_game_max_day` means new. A save file name (or a late day) means an old save: it gets the config defaults and no menu. A new game opens the menu after the intro (`currentUIMode` 0) and pauses (`pauseGame`).
- **Hold gate:** while a new game waits for the menu, the invasion feature runs no daily step (no "Pick the difficulty" banner, no clock). `invasion.set_hold_gate`.
- **Begin** (or the Close button) stores the four values in the mod state of `invasion` (`difficulty` + `difficulty_chosen`, `first_raid_years`, `size_class_fixed`, `great_raids`, `settings_applied`), un-pauses (`unPauseGame`, then `changeGameSpeed(begin_speed)`: a new game starts at speed 0 and `unPauseGame` alone does not run it) and sends `disable_autosave` again (`HarnessAutosave`). The mod never calls a save function.
- **Effects:** `first_raid_years` N: the season roll of `invasion` starts in year N+1 (`plan.should_raid` argument `first_year`). `size_class_fixed` 1 to 3: the plunder raid has that class (0: random). `great_raids` 0: no clock, no clock banner, no waves; the raid widget shows "Great raid: off".
- A menu that cannot open (a missing pak) logs the reason, applies the defaults and does not pause.
- Registered mod state defaults keep the old behaviour (year 2, random size, great raids on). The config defaults (Normal, 2 years, Medium, On) are written by the menu, by `scenario_settings_skip` and for an old save.
- Commands: `scenario_settings_state`, `scenario_settings_skip` (defaults, closes the menu), `scenario_settings_set` (any of `difficulty`, `first_raid_years`, `size_class`, `great_raids`), `scenario_settings_open`, `scenario_settings_click` (test: `action` choose, defaults or begin).
- Tests: `test_fakegame_scenario_settings.py`; test scenarios `scenario-settings-new-game-menu` (`--new-game --pak raidmenu`), `-first-raid-delay`, `-great-raids-off`, `-load-keeps-settings` (needs the guarded `save_game`; not run yet).
- A test scenario on a fixture (a loaded save) never sees the menu. A fixture counts as an old save and gets the defaults (first raid in year 3): a test that needs the raid in year 2 calls `scenario_settings_set first_raid_years=1` first.

### raid_behavior (M03)
Steers the larger Hussite raids and tracks every raid that the invasion feature spawns. A native raid is only tracked: the mod does not steer, rout or remove it. A raider counts as living only while the game unit census counts it (its squad is known to `HarnessUnits.squadMap`; a dead or uncounted unit is gone). The loot of a dead raider stays with the body (the corpse pit change `spike-corpse-pit-loot` will return it), and a bandit squad raid is not sent home by the mod. Numbers live in ModState and in the log line `RAID_BEHAVIOR`. Other features listen to it (for example `sack_and_terms`, `tribute`).
Store tiers and steal (change `add-raid-storage-tiers`): `config.raid_behavior.store_tiers` maps an EBuildingType to a tier. Tier 1 is the storehouse (6) and the granary (72); tier 2 is the manor modules (50, 57, 58, 81, 82, 83, 95, 98). `world.plunder(amount, tiers)` takes goods from tier 1 stores only, the store with most goods first. The baron steal (`rules.steal_amount`, `config.raid_behavior.steal`) runs once a game day for a lord raid of kind plunder (goal 100) or great (goal 300): each living raider farther than `threshold` (20000 game units, 200 m) from the battle marker (the lord anchor) takes `rate` (10) goods, up to the goal. `stolen` is in the raid summary. A game raid (native `spawnRaiders`) has no mod steal and may rob the manor store; the mod does not protect it.
Commands: `raid_behavior_state` (also shows `steal` and `store_tiers`), `raid_behavior_claim_back`, and test helpers `raid_behavior_test_set_leave`, `raid_behavior_test_take_region`, `raid_behavior_test_kill_raiders`.
Carry cap (change `add-raid-carry-caps`, #275): the cap acts on Hussite raids only. The plundered goods of a Hussite raid never exceed `carry_cap` (10) times its raiders at the start, and `carry_cap` is also its loot goal (the leave rule and the plunder tick use it). Native raids keep the game's own loot: the native AI resets `ItemsLooted` of a raider on a raid job to about 5 within a few game seconds, so the mod does not write it. Bandit role raids have no cap. Facts from the spike: `ItemsLooted` is a plain item count with no good; role raids (`spawnArmy`) do not use it and grow `plundered` instead. `raid_behavior_state` shows `carry_cap` and `raid_type` of each raid.

### bandits (M04)
Low approval lowers Public Order. Low Public Order turns families into bandits. The mod writes `Region.publicOrder = natural - debuff`, and takes the value the game writes back as the new natural value. The conversion uses the `homeless_rebel` route. The tick runs once per season change, and the last season is saved in ModState so a load does not repeat a season. The player can buy a converted family back.
Commands: `bandits_state`, `bandits_set_approval`, `bandits_tick_now`, `bandits_buy_back`.

### unit_balance (M05)
Changes unit values: armor, weapon, reach and veterancy. A new unit with low def gets def and block cut by a factor. An armored unit gets a weapon bonus. Long reach and experience add att and def. The feature polls known units because no spawn hook exists and a live write is lost for units that spawn later (specs 25 and 28). A known unit costs one read.
Commands: `unit_balance_state`, `unit_balance_set`, `unit_balance_apply`.

### vassals (M07)
Keeps a registry of vassal slots in ModState: region, lord name and start day. The game goal is Endless, so a claim never ends the game (spec 26). Keep peace, policy (it scales the tribute), loss, sack and restore of a vassal are implemented. A Hussite sack (a long siege, see tribute) collapses the buildings of the vassal region until 80 percent are ruins (`sack_wipe.ruin_share`), then deletes all villagers with `ManorCore.remove_families`, frees the slot (reason `wiped`) and sends a refugee wave. The land stays a village of rubble; the mod never writes the owner. A `wiped<N>` record outside the slots remembers the region. `vassals_restore` costs 100 silver, raises the village to 5 families and spawns 100 logs, 200 planks and 100 rubble stone; the restored vassal has the flag `rebuilding` and pays no tribute until 50 percent of its old buildings stand. A vassal has no loyalty: it survives or dies. Old saves hold `loyalty` and `submitted` entries in the registry; ModState keeps them as unknown entries and the feature ignores them.
Commands: `vassals_state`, `vassals_claim`, `vassals_set_keep_peace`, `vassals_set_policy`, `vassals_lose`, `vassals_sack`, `vassals_restore`, `vassals_region_census`, `vassals_set_goal`.

### sack_and_terms (M06)
Files: `init.lua` (sack), `terms.lua` (terms), each with a `*_rules.lua`. When a role raid begins to leave because it won, the town loses a share of buildings and families, the open offer of terms closes and the same raid offers no new terms (no terms after a sack of the player). The mod takes no goods; a fire may destroy part of the goods of a burned store (11 to 60 percent measured). Villagers put out a sack fire unless enemy soldiers are near, so the default method is `collapse` (rubble at once). The share grows with difficulty. Terms are a first form (marked TBD in the source). The fallback capital was removed (capital moves are not part of the game, owner decision 2026-10-20).
Commands: `sack_state`, `sack_now`, `sack_set_fatal`.

### tribute (M08)
At each season change each handed-over vassal pays goods into the player stores, as a share of a production formula. No goods move between regions. The mod adds goods to a home store. A subjugation raid on a vassal region that holds 8 game days with at least half its units alive starts the sack of the houses of that vassal (see vassals). A restored vassal pays no tribute while it is rebuilding.
Commands: `tribute_state`, `tribute_tick_now`, `tribute_test_raid_result`.

### refugees (M09)
A lost vassal (wiped by a sack) sends a wave of refugee families to the home region: 50 percent of its families (`share_min` and `share_max` are both 0.50), five families a call, three calls at most. Families arrive through `settleRegion` (five families a call, the homeless tent). The game lowers approval and feeds them. Another feature calls `send_wave(vassal_families)` when a vassal is lost. The feature reuses `features.bandits.world.rebel`.
Commands: `refugees_state`, `refugees_set_timeout`, `refugees_vassal_lost` (test path), `refugees_send_wave`.

### finite_resources (M10)
Home deposits (iron first) are a mod-owned stock. The mod counts what player buildings produce (`ProductionTrackerComponent:getGoodsProducedOver`). When the stock is used up it sets the production limit of the good to 0 for the player region (`Region:setProductionLimit`). Goods from vassals do not count and are not blocked. Spike note: `openspec/changes/archive/2026-10-16-legacy-m10-finite-resources/implementation-notes/iteration-01-iron-deposit.md`.
Commands: `finite_resources_state`, `finite_resources_test_set`, `finite_resources_test_clear`.

### manor_stronghold (M13)
The manor is the safest store. The store is owned by the mod (spec 12): `HarnessManor` keeps goods in the building inventory and refuses a put above the capacity. This feature sets the capacity from the tech tree bonus. `retinue.lua` and `squads.lua` add retinue squads above the native limit of 12 men, with `spawnArmy` and the player pawn as owner. The mod pays the silver and keeps the squad ids.
Commands: `manor_state`, `manor_put`, `manor_take`, `retinue_state`, `retinue_hire`, `retinue_squad_hire`, `retinue_squad_state`.

### tech_tree (M12)
Two exclusive paths (Oppression, Prosperity). The nodes come from `data/tech_tree/tree.json`. The player picks one path and unlocks nodes for free. One node slot opens for each settlement level. Lua applies the effects through other features: bandits, unit_balance, manor_stronghold, vassals and tribute (this is why it has six requirements). Laws and vassal policy are set here. A bad data file stops the load of this feature with a clear message.
Commands: `tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock`, `tech_tree_enact_law`, `tech_tree_repeal_law`, `tech_tree_set_vassal_policy`.

### tech_tree_widget (M12 iteration 02)
Built on the base menu: a Tech button in the bottom bar opens it; F9 stays as a shortcut.
The menu of the tech tree. `techmenu_P.pak` holds a cooked Widget Blueprint with a pool of node buttons on a canvas (`ue/make_tech_widget.py`). Lua labels, shows, hides, colours and moves the buttons from the nodes of `tech_tree`. F9 opens and closes it (`toggle_key` in config); the key only sets a flag, the scheduler tick toggles. Scenario `tech-tree-widget-key` presses the real F9 key (`--pak techmenu`). A click calls `tech_tree`.
Commands: `tech_tree_widget_open`, `tech_tree_widget_close`, `tech_tree_widget_state`, `tech_tree_widget_press`.
Tooltip (change `add-tech-tooltip`): `init.lua` calls `SetToolTipText` on the `Border` of each node and law button. The text is `lines.effect_lines(source, tree)`: one line for each effect of `tree.json` (percent kinds as a signed percent, add kinds as a signed number), then "Opens vassal policy ..." lines. `tech_tree_widget_state` lists the tooltip of each button. Lua only, no pak change. Test scenario `tech-tree-widget-tooltip`.

## Base menu
Change `add-mod-menu-access-rule` (#308), file `core/menu.lua`. All mod menus (`raid_widget`, `tech_tree_widget`, the tribute menu of `liege_influence`) register with `core/menu.lua`. A menu gives its id, a short label, the pak widget class and two functions: `on_open(widget)` (attach the click buttons, show the first values) and `on_close()`. The base menu does the rest:
- **Bottom bar button.** It finds the HUD widget `MainUICPP_C`, its `HorizontalBox` `main_tabs_HB`, and adds a clone of the game's own button class (`mainTabButton_C`) after the game's buttons, with a small text label. The click is the hook on `mainTabButton_C:HandleClicked` (it fires for all buttons of the class, so it matches the clone by name and only queues the click). A load makes a new HUD; a 1 s job adds the buttons again.
- **Backdrop.** A full-screen `Button` (z-order 450, dimmed) under the content (z-order 500) blocks clicks to the game. The content Borders are set to `SelfHitTestInvisible`, or a click on the empty menu background would reach the game. The backdrop has no click callback.
- **Close button.** A clone of the bar button, top left, above the backdrop. Pressing the key (F8, F9) or the menu's own close button also closes.
- **One menu at a time.** Opening a menu closes the open one.
- Commands: `menu_state`, `menu_open`, `menu_close`, `menu_press`. `menu_state` shows the buttons, the hover and the errors. Tests: `test_fakegame_menu.py`, `test_menu_widget_sites.py`, test scenarios `menu-smoke` and `menu-base`.
- The game has no click callback for a widget made at run time: do not use `OnClicked:Add` (crash, see [engine limits](../concepts/engine-limits.md#mod-menus-bottom-bar-button-and-click-blocking-308)).

## Shared patterns

- Split of files: `rules.lua` is pure logic that fake-game tests run without the game. `world.lua` touches game objects. `init.lua` wires state, scheduler jobs and commands.
- Season-change ticks (bandits, tribute) store the last handled season in ModState. A load must not repeat a tick.
- Both widget features obey the rule: game objects only on the game thread, no `LoopAsync` of their own.
- Key binds: a `RegisterKeyBind` callback runs on the input thread, not the game thread. It only sets a flag (`menu.request_toggle`); the base menu tick on the game thread reads it and toggles the menu. Lua work in the callback raced with the game thread and crashed the game in `luaH_getint` (F9, issue #245, [f9-key-crash.md](../../../openspec/changes/archive/2026-10-16-legacy-m12-tech-tree/implementation-notes/f9-key-crash.md)).
- A feature that needs a game fact not yet known has a spike note: in `openspec/changes/<change-name>/notes/` (open or archived changes), or in the legacy `docs/mod/M<NN>-<feature>/implementation-notes/`. Read that note before you change the code.

## Tests

- Fake-game tests: `harness/tests/test_fakegame_<feature>.py` (`modstate`, `bandits`, `invasion`, `tech_tree`, `vassals`) and rule tests such as `test_bandits_rules.py`, `test_invasion_plan_roles.py`. Run: `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"`.
- Real-game scenarios: the table above. Run them as in [Scenario run](../workflows/scenario-run.md).
- Command contracts: [Mod commands and state](../concepts/mod-commands-and-state.md).
