# Spec 10: Invasion Mode testability (harness upgrade for 90% automated verification)

Status: draft (2026-10-10). Goal set by the user: improve the harness so that about 90% of the testing of the Invasion Mode brief can be done by agents.
Source brief: "Manor Lords: Invasion Mode (Design Brief)", 2026-10-10 (kept by the user; the criteria below are derived from it).
Roadmap: continues `docs/specs/00-harness-overview/README.md` (the 90% goal), builds on specs 03 to 09.

## Goal
Make the harness able to verify the Invasion Mode brief with measurable, repeatable tests, and make the share of automated verification **visible and measurable**.
Today the harness can run scenarios, control time, sample state, assert ranges, create a few situations, and compare runs. It cannot yet observe or drive a battle, a raid cycle,
a sack, or years of game time. This spec lists what is missing and builds it.

## Non-goals
- Building Invasion Mode itself (Lua mod, pak content). This spec builds only what is needed to test it.
- Judging balance, feel, fairness or visuals. Those stay human (they are listed below as H).
- Save and load compatibility tests that need a save function (forbidden, see `CLAUDE.md`).

## What "90%" means here
1. The brief is turned into a **criteria list** (below, and as data in `criteria.json`). Each criterion states a measurable game state or event.
2. Each criterion is marked **A** (automatable), **P** (partly: the numbers can be checked, a person judges the rest) or **H** (human).
3. A criterion has a **verified test method** when a scenario or a spike proves that the needed observations and actions work in the real game
   (on a stand-in with the base game's raids and bandits, because the mod does not exist yet).
4. The target: **at least 90% of the A and P criteria have a verified test method**, and at least 90% of all criteria are either A, P or have an explicit reason for H.
   A tool (`coverage.py`, see U8) prints this number from the criteria list and the scenarios, so the claim can be checked.
5. When the mod exists, each scenario must pass against it. That is the later "90% passing" measure.

## Criteria matrix (derived from the brief)
`criteria.json` is the data form of these tables. Fields per criterion: `id`, `title`, `pillar`, `mark` (A, P or H), `method`, `blocked_by` (null or the missing system), `spikes` (ids like S1), `upgrades` (ids like U1), `method_verified` (true only when a spike or scenario proved the method in the real game), `verified_by` (note paths or scenario names as evidence), `reason_human` (required for H). `coverage.py --check-spec` checks that ids, titles and marks agree with the tables.
Legend: A automatable, P partly, H human. "Method" is what the harness must be able to do. IDs are used by scenarios (`COVERS`).

### Threat clock and scouting
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| T1 | A raid is announced N days before it arrives, and it arrives within a tolerance of the announced day | A | read the raid timer, read the inbox or alert, advance time, detect arrival |
| T2 | The announced size is within 20% of the spawned size | A | count units by side |
| T3 | The announced type matches the composition (units by type) | A | units by type and faction |
| T4 | The countdown is visible in the UI | P | screenshot, plus reading the widget text if a widget exists |
| T5 | Raid timing follows the season rules (Cuman summer, Norse spring and autumn) | A | set the day, run a simulated multi-year schedule, record raid days and seasons |
| O1 | An outpost reveals a raid only inside its own border | A (blocked until outposts exist) | outpost objects, region of each raider |
| O2 | Raiders hit the outposts first | A (blocked) | first target region of each raid |
| O3 | A lost outpost cuts trade and blinds scouting | A (blocked) | trade value, visibility flag |
| O4 | An unprotected outpost may pay tribute and leak intel | A (blocked) | state flags over time |

### Raid behavior
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| R1 | Each raid has one objective and one breaking point | A | per-raid state log |
| R2 | Loot carried per raider stays within the cap | A | goods carried per unit (`ItemsLooted` or equivalent) |
| R3 | Loot drops where a looter dies, and peasants can recover it | A | kill a unit, read ground goods |
| R4 | Retreat triggers work: full loot, morale break, timer end, leader dead | A | force each condition, observe the state change |
| R5 | A captive is freed when the captor is killed or routed in time | A (needs a captive system) | captive state, kill captor |
| R6 | Raiders go for the nearest high-value stockpile (bait works) | A | target choice versus stock positions |
| R7 | A guarded, locked granary loses less per trip than an open barn | A | stock deltas per trip |
| R8 | Burned buildings become ruins, and rebuild costs partial goods | A | building state, rebuild cost |

### Combat and balance
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| C1 | Counters work: casualty ratios of spearmen against horse archers (and shield wall against shock infantry) fall in a range over N runs | A (statistical) | casualties by type, N-run A/B |
| C2 | Veterancy persists across fights | A | `combatExperience` before and after |
| C3 | Unit stat changes (data) take effect | A | read unit rows (`DT_units`), compare with expected values |

### Sack and defeat
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| S1 | A lost battle removes a share of buildings, stock and people within the configured percent | A | counts before and after, a way to remove buildings, goods and people |
| S2 | The run continues after a sack (no game over) | A | game state, victory status |
| S3 | Repeated sacks inside the window are fatal | A | repeat, read the game over state |
| S4 | Evacuation moves families, grain and units to the fallback | A (blocked until outposts) | counts in both places |
| S5 | Tribute terms apply (payment, hostages, vassalage with yearly tribute) | A | treasury and flags over time |

### Pressure systems and difficulty
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| P1 | Laws and pacts apply their costs and benefits | A | economy and defense metrics before and after |
| P2 | Fear and hope (morale meter) follow the threat | A | approval and morale metrics against the clock |
| P3 | Refugees add workers and mouths | A | population, food use |
| P4 | The war economy toggle shifts workers | A | worker counts by building type |
| P5 | Mercenaries can be hired, with cost and presence | A | hire action (`HiredMercenaryCompanies`), units |
| P6 | Season rules apply (winter pauses fighting, strains food) | A | season set, observation |
| D1 | Tiers change size, frequency, variety and targeting | A (statistical) | N-run comparisons across tiers |
| D2 | A warlord who escaped returns stronger | A | state carried between raids |
| D3 | At top tier raiders retreat only when the leader dies | A | force and observe |

### Defense and the manor
The current castle (manor) system does not allow a real defense (user note, 2026-10-11): it cannot store goods, and normal buildings cannot be built inside it, so the player cannot wall in the city.
These two criteria are the acceptance scenarios of spec 12. Either one may be met; both is better.
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| M1 | The manor can store goods: goods can be put in, kept and read back from the manor | A | stock per manor module before and after a put and a take; stock survives game days |
| M2 | Normal buildings (burgage plots, industry) can be built inside the manor area, so the player can wall in the city | A | placement inside the manor area succeeds with the workaround and is refused without it (A/B) |

### Quality and feel
| ID | Criterion | Mark | Method needed |
|---|---|---|---|
| Q1 | The game does not crash over a simulated 2-year run | A | soak scenario with pop-up handling |
| Q2 | A large battle keeps the game responsive (tick rate, no stall) | A | game clock rate against wall time during 300-unit battles |
| Q3 | The telegraph creates dread; the sack size feels fair; the mode is fun | H | people |
| Q4 | Cuman visuals, animations, UI readability | P | screenshots, a person judges |

Blocked criteria: outposts (O1 to O4, S4), captives (R5) and tribute (S5) are systems that the base game does not have (no way to found an AI village was found in the game data). The MOD will build them.
They stay in the matrix as A (blocked). They count against the 90% until their test method is verified. The harness does not need the base game to have the system: it needs a **proven way to observe and drive
the state that a mod defines** (U10). That is proven with a small stand-in mod (a Lua mod that implements a toy outpost, captive and tribute state and exposes it through the same contract the real mod will use).
When the real mod exists, the same scenarios run against it. A blocked criterion is therefore verified (method) by the stand-in, and passing (mod) only later.

## Harness gaps and upgrades (U)
| ID | Upgrade | Why | Covers |
|---|---|---|---|
| U1 | **Telemetry v2**: units by side, type, role and state; raid state; carried goods; buildings by state (damaged, burning, destroyed); stock totals; trade value; morale and approval; configurable interval (1 s during battles); compact lines | Today telemetry has region values, player values and the date only | T2 T3 R1 R2 R4 R8 C1 C2 S1 P2 P4 Q2 |
| U2 | **Actions v2**: set the raid timer, spawn a raid of a type and size, order or steer a squad, kill units, destroy or burn a building, remove goods and people, set unit stats (`DT_units` through the data helper), give goods (exists), set the day or season (exists), hire mercenaries | Scenarios must create the situations | T1 T5 R3 R4 R6 S1 P5 C3 |
| U3 | **Scenario control v2**: `run_until(condition, timeout)` in game time, pop-up detection and a way to close it, a stall detector, longer scenario limits (the cap is 120 s today), and time budgets for multi-minute scenarios | Raid cycles take minutes; the "Hunger!" pop-up pauses the clock at 8x | T1 T5 D1 Q1 |
| U4 | **Statistics for stochastic outcomes**: N-run runner with distributions (min, median, max), tolerance rules and an effect size for A/B variants (`paks`, `env`, mod on or off) | Combat is not deterministic | C1 D1 D2 |
| U5 | **Situation builder**: a scenario helper that makes a "pre-raid" state from the base fixture with actions (resources, defenders, day, season) and returns a record of what it built | We cannot save new fixtures, so situations are built at run start | T1 R6 R7 S1 |
| U6 | **Battle observer**: `watch(duration, interval)` returns a timeline of casualties by side, loot, damage and outcome, and takes screenshots at key moments | One call per battle test | C1 R2 R4 S1 Q4 |
| U7 | **Pak pipeline** (spec 09): content layer (unit rows, raid tables, text, mercenaries) | Data beyond plain numbers | C3 T4 P5 |
| U8 | **Coverage tool** (`harness/tools/coverage.py`): reads `criteria.json` and the scenario metadata (`COVERS = [...]`) and the `method_verified` flag of each criterion and prints the share of automated criteria, the share with a verified method, the blocked ones, and the last passing run of each scenario | Makes the 90% measurable | all |
| U10 | **Mod-state contract and stand-in mod**: a documented way for a mod to expose its own state and commands to the harness (each mod serves its own commands and metrics from its own Lua state through `HarnessCommands.register` and `HarnessCommands.metric` and the folder `modcmd/<ModName>/`, because UE4SS gives every mod its own Lua state; a naming rule), plus a small stand-in mod `InvasionStandIn` with a toy outpost, captive and tribute system and scenarios that observe and drive it | The mod will add systems the base game lacks (outposts, captives, tribute). The harness must test them the same way, before the real mod exists | O1 O2 O3 O4 R5 S4 S5 and every mod-defined metric |
| U9 | **Performance and soak probes**: game clock rate against wall time, with unit counts; a 2-year soak scenario with periodic raids | Q1 Q2 | Q1 Q2 |

Status of U3 and U9 (2026-10-10, branch `feat/23-scenario-control`):
- **U3 built.** `ctx.run_until` (wall or game time, stall detector), scenario limits up to 4200 s (a limit above 300 s needs `LONG_REASON`), launcher and suite timeouts that follow the scenario limit, run cap 400 (`HARNESS_MAX_RUNS`), `close_popups` and `ctx.popups`. Real scenario: `soak-days`, 3 of 3 passed. Unit tests: `test_runlib_waiting.py`, `test_runlib_popups.py`. Not verified: a game-time `run_until` against the real game.
- **U9 partly built.** The soak scenario records clock rate and process memory at start and end and asserts ranges. The 2-year run is **not** possible on the unmanaged start village (defeat at about day 350), so Q1 is verified as a method over 120 to 350 days and the rest is extrapolated. Notes: `implementation-notes/soak-results.md`. Not built: a periodic raid in the soak.

## Capability spikes (real game; each result goes to `implementation-notes/`)
Each spike answers one "can the harness do this" question on the base game, with before and after numbers. A stand-in is used where the mod does not exist.
- **S1 Raid timer (done, partial, `spike-S1.md`):** read and write `TemporalComponent.daysUntilNextRaid` and `daysSinceLastRaid`, and the raid ID lists (`defaultRaidIDs`, `eliteRaidIDs`). Does a raid spawn when the timer is zero? What arrives (units, count, side)?
- **S2 Raid spawn function (done, `spike-S2.md`):** find the signature of `spawnRaiderForce` in the jmap and call it through the helper mod. Compare with the verified `SpawnBanditSquad` (+18 units).
- **S3 Observation of units (done, partial, `spike-S3.md`):** read side, type, role, state, position and carried goods of units. Find what `ItemsLooted` holds.
- **S4 Steering:** can a spawned squad be ordered or steered (squad component functions, `targetSquad`, `lastSquadTargetPosition`), or only observed?
- **S5 Loot drop (done, partial, `spike-S5.md`):** kill a unit that carries goods and read the ground goods.
- **S6 Sack primitives (done, `spike-S6.md`, `spike-R3.md`):** destroy or burn a building (`onFire`), remove goods from a building's inventory, remove people, count each. Result: all three work from Lua and are counted before and after. `StartFire` and `collapseBuilding` make a building rubble (type 75, it stays in the list; a fire also destroys its goods); `consumeGoodNoCheck` removes goods one unit at a time from one named store; `just_die` on all members of a family removes the family at once. Not possible: the rebuild cost of a ruin (R8), a real guard or lock (R7) and loot on the ground (R3) do not exist in the base game or cannot be read, so R7 and R3 are verified on mod-defined rules (a loss factor, a stand-in ledger).
- **S7 Unit data (done, `spike-S7.md`):** the table is `DT_UnitTemplates` (no `DT_units`). `HarnessDataTable` lists its 25 rows and 6 number fields and writes them live. Writing `maxSize` 32 -> 10 changed the next squad to 10 units (scenario `unit-data`, 3 of 3). There is no hit point field. `spawnArmy` with a template name and an owner pawn spawns typed units on the player or the bandit side (this also answers the type limit of S2). Related: `spike-P5.md` (mercenaries: `hireMercs`, cost paid, units at once), `spike-C2.md` (veterancy), `spike-C1.md` (counters).
- **S8 Pop-ups and stalls (done, `spike-S8.md`):** find the function that closes the "Hunger!" and similar pop-ups, or a way to prevent them, so long scenarios do not stall. Result: the Accept handler of `popupMessageWidget_C` closes the pop-up and the game resumes at the old speed (action `close_popups`). Feeding the village prevents the hunger pop-up. A village that is not fed is defeated at day 137 (the clock then stops for good). Two types seen: `hunger`, `cold`.
- **S9 UI countdown (done, `spike-S9.md`):** can a widget be created from Lua, or can the alert system carry a countdown text? Result: `PawnCPP:playEventMessage(FName("Default"), text, text2)` shows a banner ("Raid in 2 days") and the widget `genericAchievement_EventMessage_C` holds the text, so the harness reads it back and takes a screenshot (scenario `ui-countdown`, COVERS T4, 3 of 3). The banner fades after a few seconds; the look is Q4 (human). A custom widget was not tried.
- **P3 Refugees (tried, not verified, `spike-P3.md`):** no refugee function or event exists in the base game. `Region:growPopulation()` changed nothing in the start village (no housing), and housing cannot be placed with one click. P3 stays unverified.
- **R8 Rebuild cost (done, `spike-R8.md`):** a rebuild is "demolish the ruin, place the building again". The new site lists its goods in `constructionGoods` (Dunghill: Planks 4), and a lower `amt` makes the builders use less (4 -> 2). Hidden scenario `rebuild-cost` (COVERS R8, real mouse, 3 of 3).
- **S10 Performance (done, `spike-S10.md`):** spawn 300 units and measure the game clock rate at 1x and 8x.
- **S12 Manor (spec 12):** survey the manor system (modules, planner, the building rule, storage) and test the workarounds for criteria M1 and M2. Findings go to the notes of spec 12.
- **S11 Baron model:** the base game has a baron that acts as a hostile off-map AI (user note, 2026-10-10). Find how it decides, sends and controls its forces (demands, claims, armies, diplomacy state). Can invaders reuse it as the adversary model (a new baron or faction with its own objectives)? This could replace a custom raid AI (S1, S4) and give outposts a base model (O1 to O4). Write findings to `implementation-notes/baron-model.md`.

## Plan
1. DONE: this spec, `criteria.json` and the coverage tool (U8), so progress is measurable from day one. Start value: `implementation-notes/coverage-baseline.md`.
2. PARTLY DONE (2026-10-10): spikes S1, S2, S3, S5 and S10 ran on the base game (notes `spike-S1.md`, `spike-S2.md`, `spike-S3.md`, `spike-S5.md`, `spike-S10.md`).
   Results: the raid timer can be written and a raid of 18 units spawns on the day tick that brings it to 0; `spawnRaiders`, `spawnEliteRaiders` and `spawnBanditCamp` work with a plain Vector table;
   units can be counted by side, role, region and loot in about 10 ms; units can be killed with `just_die`; 1x clock rate stays at 1.02 up to 661 units.
   Not possible: unit type or template, raider versus bandit split, unit health, choosing raid type or size, announcement of a raid in the base game, loot on the ground (not found).
   S4, S7 and S9 are still open (S6 is done, see below; S8 is done). Coverage after these spikes: 3 of 37 A and P criteria verified (T2, R2, Q2), see `coverage-after-raids.md`.
   Spikes S1 to S12 in the real game (one agent at a time uses the game), with results in notes. Update the matrix marks and `METHOD_VERIFIED` for each criterion.
3. Build U1 to U6, U9 and U10 in order of what the spikes show works. Unit tests with fake bridges. Each gets a real scenario on a stand-in.
4. Reference scenarios (stand-ins on the base game) for every A and P criterion that has a method, each tagged with `COVERS`.
   - U4 built (2026-10-10): `run.py --pak/--env`, suite `variants`, `suitelib/stats.py`, the A/B report and the `expect` rule, `ctx.metric`. Unit tested with a seeded stand-in; NOT verified: a real A/B on the game and a real pak in a run. Notes: `implementation-notes/ab-statistics.md`.
   - U10 built (2026-10-10): the mod-state contract (redesigned 2026-10-10 after the real-game finding that every mod has its own Lua state: `HarnessCommands` in `mod/shared` starts a poller in the state of each mod, request files in `modcmd/<ModName>/`, built-in commands `harness.list_commands` and `harness.metrics`, metric naming `<ModName>.<metric>`), `ctx.mod` (`runlib/modstate.py`), the stand-in mod `InvasionStandIn` and the scenarios `standin-outposts`, `standin-captives`, `standin-tribute`. Unit tested in the fake game kit and with fake bridges. **PENDING: the real-game run of the three stand-in scenarios.** Until it passes, `method_verified` stays false for O1 to O4, R5, S4 and S5 (they are listed as `planned` in `verified_by`). The first real run proved that each mod has its own Lua state; the contract was changed so that each mod serves itself, and the new design is pending a real run. Notes: `implementation-notes/mod-state-contract.md`.
   - U10 follow-up built (2026-10-10): the second stand-in mod `RaidStandIn` models the mod-defined raid logic (director with a timer you can set, announcement, seasons, tiers, retreat triggers, bait targeting, warlord, sack rule, laws, morale meter, war economy) with a seeded random generator and a toy clock that follows the game days and can be set by command. Six scenarios (`raid-timeline`, `raid-seasons`, `raid-behavior`, `raid-tiers`, `raid-sack`, `raid-politics`) cover T1, T3, T5, R1, R4, R6, D1, D2, D3, S2, S3, P1, P2, P4 and P6, including N-run comparisons across tiers and a suite for the A/B runner (`raid-size-ab`). Unit tested in the fake game kit, with broken-rule cases. **PENDING: the real-game run.** Until it passes, `method_verified` stays false for these 15 criteria (`planned` in `verified_by`). Not covered, because they need the real game: C1, C2, C3, P3, P5, T4, Q1, Q4 (R3, R7, R8 and S1 are covered by the S6 scenarios, see below). Notes: `implementation-notes/raid-standin.md`.
   - Built on branch `feat/31-ui-refugees-rebuild` (2026-10-10): `HarnessUi` (banner text with read-back) and `HarnessBuild` (construction site goods, ruins, lower cost), `HarnessActions` version 11, actions `show_message`, `read_message`, `list_messages`, `building_sites`, `ruin_building`, `demolish_ruins`, `set_site_cost`, scenarios `ui-countdown` (T4) and `rebuild-cost` (R8, hidden). Coverage: 35 of 37 A and P criteria verified (95%), see `coverage-after-s9-r8.md`. P3 not verified (`spike-P3.md`).
   - S12 part done (2026-10-11, branch `feat/33-manor-spike`): shared module `HarnessManor`, `HarnessActions` version 12, actions `manor_state`, `finish_manor_site`, `manor_put`, `manor_take`, `manor_stock`, hidden scenario `manor-storage` (M1, 3 of 3 real runs). M1 method verified (mod-defined store on the Keep inventory, harness shortcut to finish the Keep). M2 not verified: see spec 12 notes. Coverage: 36 of 39 A and P criteria verified (92%), see `coverage-after-manor.md`.
   - S6 built (2026-10-10, branch `feat/27-sack-primitives`): shared modules `HarnessSack` and `HarnessLoot`, `HarnessActions` version 8, actions `sack_census`, `sack_buildings`, `sack_goods`, `sack_people`, `sack_village`, `drop_loot`, `loot_piles`, `recover_loot`, scenarios `sack-village` (S1), `sack-ruins` (the ruin state of R8; not tagged with COVERS, because the rebuild cost is not verified), `sack-store-trip` (R7) and `loot-drop-recovery` (R3, stand-in ledger). Unit tested in the fake game kit and with fake bridges. Real-game results: `implementation-notes/spike-S6.md`. R8 stays unverified: the rebuild cost cannot be read.
   - U2, U4, U6 and U7 part built (2026-10-10, branch `feat/28-unit-data-combat`): shared module `HarnessBattle` (typed spawn, battle registry, casualties and experience, mercenary hire), `HarnessDataTable` for the unit table, `HarnessActions` version 9, actions `datatable_rows/write`, `spawn_units`, `battle_state`, `clear_battle`, `set_squad_experience`, `mercenary_offers`, `hire_mercenaries`, `runlib/fights.py` (battle observer), `ctx.variant_option`. Scenarios `unit-data` (C3), `mercenary-hire` (P5), `veterancy` (C2), `counters-ab` (C1) passed 3 of 3 real runs each; suite `counters-ab` (8 runs) showed a real, measured A/B difference (spear 0.72 against heavy 0.15 player loss rate). Limits: no horse template in the base data (C1 covers the templates that exist); no hit points; a pak change of the unit table is not tried; mercenary upkeep is not verified.
5. Run the coverage tool. Close gaps or move criteria to H with a written reason. Record the final number.
6. When the mod exists: run the same scenarios against it (a later spec).

## Open questions
- Does the base game accept writes to the raid timer and raid ID lists, or only reads? Answered for the timer: it accepts writes and holds them. The ID lists were only read.
- Can an agent steer enemy units, or only spawn and observe them? This decides R1, R4, R6 and R5.
- Is there any way to found an AI village at runtime (O1 to O4, S4)? If not, the brief must change or a native mod is needed.
- Which time scale keeps a raid cycle inside a scenario of a few minutes?

## Acceptance criteria
- `criteria.json` lists every criterion above with mark, method and status. `coverage.py` prints the shares, and a unit test checks its arithmetic.
- Every spike has a note with real numbers (or "not possible" with the evidence).
- At least 90% of the A and P criteria have a verified test method. A blocked criterion counts as verified once the stand-in mod (U10) proves the observation and drive method for it. Blocked criteria are listed openly until then.
- Every upgrade U1 to U6, U9 and U10 has unit tests and at least one real scenario that passes 3 of 3 runs.
- The final report states the measured coverage and what is human only.
