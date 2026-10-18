# Coverage criteria of the Invasion Mode brief

The criteria matrix that `harness/tools/coverage.py` reads. `--check-spec` compares the tables here with `criteria.json` in this folder. Moved from legacy spec 10 (`docs/harness/10-invasion-testability/README.md`) by the change `move-coverage-criteria-to-openspec` (#279). Update a mark here and in `criteria.json` in the same commit.

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
| M1 | The manor can store goods: goods can be put in, kept and read back from the manor, and a storehouse or granary worker serves the store | A | stock per manor module before and after a put and a take; stock survives game days; the manor storage building has a worker slot with the same role as a storehouse or granary worker, a family is assigned, and that worker carries goods in or out of the store |
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

