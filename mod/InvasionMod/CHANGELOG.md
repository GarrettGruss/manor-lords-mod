# Changelog

Each entry names its feature. Format: Keep a Changelog.

## [Unreleased]

### Fixed
- Feature `tribute` (#517): vassal tribute pays goods again. It called `raid_world.deposit`, which was removed from `raid_behavior`. It now deposits with its own helper (`addToInventory`, read back from the store inventory). No change to the rules.

### Changed
- **liege_contracts (new), liege_influence:** the liege screen offers three contracts at each start of spring. You pick one. Completed contracts pay influence, silver, goods, public order or a tech point at once. A contract that is not complete when winter begins costs 500 influence. You can no longer buy influence with silver. The arms shipment is unchanged.
- **Tech tree (window):** the tech window has a new layout: a header with the title, the tech picks counter ("1 free (0 of 1 used)") and a Close button; column heads I to IV (first to fourth tech); the rows Oppression, Prosperity and Common, with a card for each tech (name, status, effects, its law and an Enact or Repeal button) and links between the techs of a path; a laws strip ("N of 2 max") with a Repeal button for each law in force; and a footer with the last result (for example "Martial Law refused: no free pick.") and "One tech pick each spring. The path you swear to is final." The three text lines at the top are gone. Common techs can be clicked before a path is chosen.
- **Tech tree (picks):** one pick at the start and one pick at each start of spring (banked when unused) replace the node slots of the settlement level. Every unlock of a path node or a common tech costs one pick. The pick state is saved with the game.
- **Corpse pit (loot is now opt-in):** the pit pays loot only while the law Strip the Dead is in force. Before, it always paid the share of Hussite raiders.

### Added
- **Tech tree (common techs and laws):** Corpse Robbing, Armory Census and Night Watch need no path and can be unlocked before a path is chosen. They open three laws that count toward the limit of two laws:
  - Strip the Dead: bodies of bandits at the corpse pit pay loot (a sword and a small shield, and in half of the bodies a helmet) and each looted body costs 1 Public Order.
  - Disarm the Peasantry (approval -3): each game day the weapons of the homes go to the storehouse.
  - Curfew (approval -4): banditry costs half as much Public Order for each homeless family.

### Removed
- **liege_influence:** the tribute button, the command `liege_send_tribute` and the config values `influence_per_unit` and `tribute_button_amount`.

## [0.1.0] - 2026-10-24
First release for play testers. The mod turns Manor Lords into "The Hussites Are Coming": a growth game where Hussite armies raid you and your vassals.

### What the mod does
- **New game template and start menu:** the New Game screen has a 6th template, "The Hussites Are Coming". A new game opens a start menu where you pick the raid level for yearly raids, great raids and vassal raids (0 off, 1 easy, 2 medium, 3 hard). The game stays paused until you click "Begin the game". You start with 10 people and 300 silver.
- **Raids:** no raid comes in the first game year. From the second year, one raid can come each year (a roll at each season change). Raids are Hussite armies of mixed units, led by an AI lord. A banner warns you 30 game days before a large plunder raid or a subjugation raid. The great raid starts at game year 10, with banners in years 7, 8 and 9. The raid menu (F8 or the Raid button) lists the next raids.
- **Raid behavior:** raiders steal goods from your tier 1 stores (storehouse, granary), never from the manor store, and carry only a limited load. Goods that raiders take go to the corpse pit when their bodies arrive there. A lost battle sacks the town; the invader may offer terms, but not after a sack of your region.
- **Vassals:** friendly AI lords run regions in your name. They pay goods each season as tribute (also iron and salt). A Hussite sack can wipe a vassal (80 percent ruins). You can pay silver to restore it. A lost vassal sends refugee families to you.
- **Public order and bandits:** the mod keeps its own public order. Low order starts a timer; when it ends, families leave and form a bandit camp. You can pay silver to bring families back. The Public Order tooltip lists the terms.
- **Tech tree (F9 or the Tech button):** two exclusive paths, Oppression and Prosperity, with nodes, laws and vassal policies. A tooltip shows the effects.
- **Liege screen:** pay silver as tribute to earn influence, and request an arms shipment (200 silver, 30 large shields and 30 spears, 180 game days cooldown; needs a built manor).
- **Manor and economy:** the manor module is a store with a capacity and tech upgrades. Home deposits of iron, salt and clay run out; vassal tribute is the lasting supply.
- **Unit balance:** unarmored units lose defence, so armor matters.

### Known limits
- English only.
- The City Building thumbnail shows on the Hussite template.
- RE-UE4SS experimental build 4.0.0-rc1 is required.
- Vassals need the game setting AI opponents above 0. With 0, the start menu shows "Warning: vassals are not enabled."
- Not verified in the real game: the tech tree tooltip on mouse hover, and the arms shipment cooldown over a save and a load.
- The terms of the Public Order tooltip are not saved over a load.

### Details by change
### Added
- Feature `scenario_settings` (change `add-game-settings-guard`, #438): guard value `vassals` and the menu warning "vassals are not enabled". See the root `CHANGELOG.md`.

### Changed
- Change `update-single-mod-pak` (#471): the Invasion Mod ships one pak, `InvasionMod_P.pak`, with all widgets and the data rows (the 6th scenario template). `raidmenu_P.pak` and `techmenu_P.pak` are removed. Run test scenarios with `--pak InvasionMod`. The release zip builds now (the release check ignores `require` of the mod's own Lua files, `HarnessAutosave` is no longer in `shared`).
### Fixed
- Feature `liege_influence` (change `fix-arms-button-manor`, #455): the arms button is disabled (grey look, clicks ignored) while no manor is built, with "Build a manor first" under it; the cooldown and silver cases use the same look. See the root `CHANGELOG.md`.

### Changed
- Feature `bandits` (change `update-banditry-bandit-camp`, #453): families that leave for banditry go to a bandit camp. One camp (18 Brigands) spawns for each leave event, at a place the game picks. The mod makes the bandit pawn itself when the game has none (bandit camps 0). The rule "one squad per 5 families" is removed.

### Changed
- Bandits public order (change `update-bandits-public-order`, #424): Every 5 families that leave form one brigand squad (18 families give 3 squads). the mod keeps its own public order (100 in a new game) and writes it to the game. Every 30 game days it adds 10 (plus the tech tree `order_bonus`) and subtracts 5 for each homeless family; each tick is logged and in the telemetry (`bandits_order`). Order under 25 starts a 90 game day timer; when it ends, up to 18 families leave to become bandits (a bandit band spawns only when the game has a bandit pawn, otherwise the mod logs it) and order rises by 25. Three banners: timer start, 30 game days before, leave. This replaces the approval debuff and the season roll. The tech tree `approval_bonus` has no effect now.
- Feature `invasion` and `raid_widget` (change `update-raid-banners`, #400): one 30 day banner for a subjugation raid and a large plunder raid, no banner for a yearly raid or the difficulty, the great raid at game year 10 with a banner in years 7, 8 and 9, the raid menu lists the upcoming raids. See the root `CHANGELOG.md`.

### Changed
- Features `invasion`, `scenario_settings`, `raid_widget` (change `update-raid-difficulty-levels`, #404): one level 0 to 3 for each raid type (yearly player raid, great raid, vassal raids) in place of the global difficulty and the Great raids switch. Level 0 turns the raid type off. Bandits, sack and terms read the highest level.

### Added
- Features `scenario_settings` and `liege_influence` (change `add-scenario-start-kit`, #425): start kit (10 people, 300 silver) at "Begin the game" of a new game, and the liege button "Request arms shipment" (200 silver, 30 large shields and 30 spears in the manor store, 180 game days cooldown). See the root `CHANGELOG.md`.
- Feature `vassals` (change `add-vassal-sack-wipe`, #341): sack of vassal houses (80 percent ruins), wipe of all villagers (reason `wiped`), refugee wave of 50 percent, and `vassals_restore` (100 silver, 5 families, goods for the rebuild). Feature `sack_and_terms`: no terms after a sack of the player region.

### Changed
- Refugee wave of a lost vassal is 50 percent of its families. A long siege of a vassal starts the sack of its houses.
- Feature `raid_behavior` (change `add-corpse-pit-loot`, #386): the body share of Hussite plunder goes to the corpse pit. See the root `CHANGELOG.md`.
- Feature `scenario_settings` (change `add-scenario-settings-menu`, #375): the scenario settings menu of a new game (difficulty, first Hussite raid after 1 to 3 years, raid size, great raids on or off), kept in the mod state. The raid menu lost its difficulty buttons. See the root `CHANGELOG.md`.
- Features `raid_widget`, `tech_tree_widget`, `liege_influence` (change `add-mod-menu-access-rule`, #308): each menu opens with one click on its own button (Raid, Tech, Liege) in the game's bottom bar. All menus use the base menu `Scripts/core/menu.lua` (full-screen dimmed backdrop that blocks clicks to the game, Close button, one menu at a time). F8 and F9 stay as shortcuts. The spike "Mods" button and its commands `spike_entry_open`, `spike_entry_state` are removed.

### Removed
- Fallback capital, loss mode `take_by_lord` and command `vassals_set_loss_region` (#341).
- Feature `vassals` and `tribute`, tech tree (change `remove-vassal-loyalty`, #344): no vassal loyalty. A vassal survives or dies. No gift order, no submission, no loyalty change after a raid, no law effect `vassal_loyalty`. The tribute share is fixed at 0.20 (`tribute.share`). Old saves are read without error.

### Fixed
- Spec 34 (#254): the tech tree and raid menu buttons report a click through a hook (shared module HarnessClickHooks, pak widget WBP_ClickButton) instead of polling. Labels refresh every 500 ms and only when they change. Scheduler tick 100 ms. Paks `techmenu_P.pak` and `raidmenu_P.pak` rebuilt (the buttons are Borders that hold a click button). Scenario `tech-tree-widget-clicks`.
- Mod M12 (#245): the real F9 key no longer crashes the game. The key callback of the tech tree menu and the raid widget only sets a flag; the scheduler tick opens or closes the menu on the game thread. Scenario `tech-tree-widget-key`.

### Added
- Mod M13.03 (#215): extra retinue squads above the native limit of 12. Command `retinue_squad_hire` pays 36 x the hire cost and spawns a player squad of `retinue_tier1` (spawnArmy); each 12 of the retinue bonus allows one squad. Command `retinue_squad_state`. Scenario `manor-stronghold-retinue-squads`, probe `probe-retinue-squads`.
- Mod M12.05 (#236): the tech tree menu lists the laws of the chosen path and has buttons to enact and repeal them (pak `techmenu_P.pak` rebuilt with a laws line and 3 law buttons). `tech_tree.view()` returns `laws`. Command `tech_tree_widget_press` calls the click handlers without the mouse. Scenario `tech-tree-widget-laws`. Real clicks: open (#203).
- Mod M10.02 (#226): salt (300) and clay (500) are finite home deposits like iron (TBD sizes). Vassals pay iron (10 per family) and salt (6 per family) with the tribute (config `tribute.finite_goods`); that supply does not reduce the home deposits. Scenario `finite-resources-vassal-supply`.
- Mod M06.04 (#224): the sack hits the region under attack (the raid target) or the home region, not the first region of the player (a fallback capital could be first). `HarnessSack` functions take an optional `region`; sack result has `region`. Scenario `sack-and-terms-sack-region`.
- Mod M10.01 (#222): feature `finite_resources`. The iron deposit (400 units, TBD) is a mod ledger fed by the building production; when empty the mod sets the player production limit of the good to 0. Commands `finite_resources_state`, `finite_resources_test_set`, `_test_clear`. Scenario `finite-resources-iron`, probe `probe-deposits`.
- Mod M02.07 (#220): vassal targets. A subjugation raid targets a vassal region when a handed-over vassal exists (the home region stays the stand-in otherwise). After 8 game days with half of its units left, the raid takes the vassal: `vassals.lose_vassal(slot, "taken")` (slot freed, refugees; the region owner is not moved). `invasion.set_vassal_provider`, `raid_behavior.active_raids`, `vassals.target_regions`. Scenario `invasion-vassal-targets`.
- Mod M12.04 (#217): laws and vassal policy gates in `tech_tree.json`. Six laws (Conscription, Forced Labor on Walls, Scorched Earth; Militia Charter, Trade Pacts, Pay Off Warbands), at most 2 in force; effects `tribute_share` and `vassal_loyalty`. `light` and `heavy` vassal policies need a path and a node. Commands `tech_tree_enact_law`, `tech_tree_repeal_law`, `tech_tree_set_vassal_policy`. Scenario `tech-tree-laws`.
- Feature `unit_balance` (M05.04, #194): config `reach_min`, `reach_max`, `reach_att_add`, `veterancy`. Commands `unit_balance_set` takes `reach_att_add`, `vet_enabled`, `vet_att_per_tier`, `vet_def_per_tier`; the state shows `reach`, `veterans`, `vet_changes`.
- Mod M08.02 (#214): protection. A raid on a vassal region that ends undefended (left by loot or time) lowers the vassal loyalty by 15; a defended one (destroyed, or left by losses) raises it by 5. `raid_behavior` gets `watch_end` and `target`. Command `tribute_test_raid_result`. Scenario `tribute-protection-and-loyalty`.
- Mod M13.02: retinue limit. Tree effect `retinue_capacity` (+12 at Veteran Levies and Militia Rights) raises the limit that scripts read and the hire gate. The native hire still stops at 12 (spike result). Commands `retinue_state`, `retinue_hire`. Scenario `manor-stronghold-retinue`, probe `probe-retinue-cap`.
- Mod M07.04 (#212): a lost vassal frees its slot and sends a refugee wave (M09 listens through `vassals.on_lost`); a vassal at loyalty 10 or less submits (the lord goes to war, tribute stops) and returns at 40. Commands `vassals_lose`, `vassals_set_loss_region`, `vassals_submission_tick_now`. Scenario `vassals-loss-and-submission`. Moving the land of a lost vassal to another owner crashed the game; the default leaves it with its lord.
- Mod M13.01 (#207): feature `manor_stronghold`. The capacity of a manor module is 200 units plus the tech tree effect `manor_storage` (+200 at Iron Hand and at Amnesty). Commands `manor_state`, `manor_put`, `manor_take`. Scenario `manor-stronghold-storage` (fixture `manor-bailey`). Spec `docs/mod/M13-manor_stronghold/iterations/01-manor-storage.md`.
- Mod M07.03 (#209): vassal policies light, fair and heavy (mod-owned, config `vassals.policies`): a loyalty change at each season change and a factor on the tribute share. Order: a gift (50 silver, +10 loyalty). Commands `vassals_set_policy`, `vassals_order_gift`. Scenario `vassals-policies-and-orders`.
- Mod M06.03 (#205): fallback capital. `fallback_move{slot}` takes a fortified vassal region back for the player (owner write), pays 150 x difficulty silver, moves 20 grain and sends 5 settler families. The vassal slot becomes the capital. Commands `fallback_state`, `fallback_move`. Scenario `sack-and-terms-fallback-capital`. The clear-owner route crashes the game and is not the default.
- Mod M12.02 (#203): the tech tree menu (key F9). Pak `techmenu_P.pak` holds a pool of 16 node buttons; Lua labels, colours and places them from `data/tech_tree/tree.json` (layout data). Feature `tech_tree_widget`; commands `tech_tree_widget_open`, `_close`, `_state`; scenario `tech-tree-widget` (real mouse, `--pak techmenu`; click steps not yet verified). Spec `docs/mod/M12-tech_tree/iterations/02-pak-ui.md`.
- Mod M09.02 (#202): a refugee wave ends `housed` when the homeless count is back at the base, or `rebelled` after `refugees.timeout_days` (45): the unhoused families (at most 6) turn into bandits through `homeless_rebel`. Command `refugees_set_timeout`. Scenario `refugees-housing-and-timeout`.
- Mod M09.01 (#200): feature `refugees`. A lost vassal sends 30 to 60 percent of its families as a refugee wave to the home region (settleRegion steps of 5 families, tent camp). Commands `refugees_state`, `refugees_vassal_lost`, `refugees_send_wave`. Scenario `refugees-wave`.
- Mod M08.01 (#197): feature `tribute`. At each season change each handed-over vassal pays goods (fish, timber) into the home stores: production (families x 20) x share (10 to 30 percent by loyalty). Commands `tribute_state`, `tribute_tick_now`. Scenario `tribute-payout`.
- Mod M12.01 and M12.03 (#195): feature `tech_tree` of `InvasionMod`. Two exclusive paths (Oppression, Prosperity) built from `data/tech_tree/tree.json`; one node slot for each settlement level; 8 draft nodes with effects on Public Order, the Public Order approval, the buy-back price and the militia attack and defence. Commands `tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock`. Scenarios `tech-tree-path-choice`, `tech-tree-militia-factor`. Spec `docs/mod/M12-tech_tree/iterations/01-path-choice.md`.
- Mod M07.02 (#191): the `vassals` feature hands a region that the player claimed and settled to a new AI lord (friendly, builds). The mod declares peace when the lord declares war (config `keep_peace`) and flags a lord that does not build (`stalled`, 10 game days). Scenario `vassals-settled-vassal`. Notes `docs/mod/M07-vassals/implementation-notes/iteration-02-settled-vassal.md`.
- Feature `unit_balance` (M05.03, #183): weapon bonus for armored units. Commands `unit_balance_set` takes `att_factor` and `pierce_add`; `unit_balance_state` shows `weapon`, `att_factor`, `pierce_add`.
- Feature `raid_widget` (M02.05, #189): the raid menu (pak `raidmenu`, key F8), commands `raid_widget_open`, `raid_widget_close`, `raid_widget_state`, config `raid_widget`. `invasion` exports `raid_info` and `pick_difficulty`; `terms` exports `summary`.
- Mod M07.01 (#187): feature `vassals` of `InvasionMod`. The mod writes goals = Endless on every start and load (a claim no longer ends the game) and keeps a 3 slot vassal registry with loyalty in ModState. Commands `vassals_state`, `vassals_claim`, `vassals_set_loyalty`, `vassals_set_goal`. Scenario `vassals-claim-without-victory`.
- Feature `invasion` (M02.06, #186): great raid phases (`gr_*` ModState keys), `great_raid.next_action`, `relief.lua`, config `invasion.great_raid` wave and final values, three `invasion_great_*` commands. `raid_behavior` exports `final_raid_ended`; a `great` raid has no plunder and no leave.
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

### Fixed
- Feature `raid_behavior`: a non-number `ItemsLooted` no longer raises an error in the unit scan (M02.06, #186).

### Changed
- Feature `mod_state`: `mod_state_dump` returns only its selftest keys.

- Skeleton with the feature loader and the stub feature `example`.
