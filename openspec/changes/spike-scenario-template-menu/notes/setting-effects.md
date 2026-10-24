# Question 3: effect of the game settings on the mod AI (tasks 4.1 to 4.3)

## Verdict

**The Invasion Mod reads none of the six settings. They drive native raids, camps and lords only.** The Hussite raid works with every value tried. One link matters: with Initial bandit camps 0 (and no camp ever made) the world has no bandit pawn, and the mod's bandit code fails ("no pawn for side bandit"). That is the camp setting acting on the mod by omission (see `openspec/changes/archive/*-spike-playtest-world-ai/notes/bandit-camps.md`, which answers it: the mod can call `spawnBanditCamp()`).

## 4.1 Map: setting to mod code

Search: `grep` of `mod/` for `gameSetup`, `raidingFrequency`, `maxBanditCamps`, `initialBanditCamps`, `AI_aggressiveness`, `adversary_baron`, `yearsUntilFirstRaid`, `numGenericAILords`.

| Setting (field) | Read by the mod code? | Native effect | Verdict |
|---|---|---|---|
| End Goal (`goals`) | Yes: `vassals/world.lua` reads and writes it through `HarnessGameSetup` (victory rules). | Victory condition. | Link (already used) |
| AI Opponents (`numGenericAILords`) | No. The mod makes its own lords (`spawn_ai_lord`). | Number of lords at the start. | Native only (vassal and raid lords work with 0: spike #430) |
| Off Map Adversary (`adversary_baron`) | No. (`raid_behavior` has a "baron steal" rule, but it only uses the name; it reads no setting.) | A baron lord that makes native raids. | Native only |
| AI Aggressiveness (`AI_aggressiveness`) | No. | Behaviour of native lords. | Native only (see A/B below) |
| Raider Frequency (`raidingFrequency`) | No (only the harness probe `HarnessRaids.readSetup`). | Native bandit raids. | Native only |
| Raider Free Years (`yearsUntilFirstRaid`) | No. The mod has its own "First Hussite raid" setting (`first_raid_years`). | Time of the first native raid. | Native only |
| Initial Bandit Camps, Random Bandit Camp spawn limit (`initialBanditCamps`, `maxBanditCamps`) | No. But the bandit pawn is made by a camp, and `ManorCore.spawn_squads` and `HarnessBattle` need it. | Camps at the start and later. | Indirect link: camps 0 gives no bandit pawn |

## 4.2 Plan and 4.3 results (small samples, ranges, not exact values)

The question was "does it change the mod AI". The mod AI is the Hussite raid (a mod lord with a spawned army, plunder and leave) and the vassal lords. One run each, in real games. Reuse of the answers of the spike #430 (fixture `playtest-noai`: AI opponents 0, baron Absent, aggressiveness 2, frequency 0, camps 0) against `base` (3 lords, baron Absent, aggressiveness 1, frequency 1, camps 1 to 3).

| Setting values | Run | Mod AI result |
|---|---|---|
| AI 0, aggressiveness 2, frequency 0, camps 0 | `q3-first-raid-playtest-noai-181628`, `q3-comp-noai-181016` | pass: plan, spawn on the planned day, 64 units, composition ok |
| AI 3, aggressiveness 1, frequency 1, camps 1 to 3 | `q3r-first-base-183129`, `q3r-comp-base-182942` | pass: plan, spawn on the planned day, 50 units, composition ok |
| same as base, aggressiveness written to 0 at run time | `menu-s-191029` (forced raid) | raid spawned (68 units), plunder 68, 68, 30 goods on the first days, 190 goods after 20 game days: the same as with aggressiveness 1 (`base-r-184008`: 156 goods in 18 days) |
| frequency written 0, 3, 2, 1 at run time (paused) | `menu-s-191029` | `daysUntilNextRaid` stayed 525 for every value: a write of the setting does not move the native timer |
| frequency 0, then `daysUntilNextRaid` forced to 2, 8 polls at speed 3 (about 12 game days) | `menu-s-191029` | the game reset the counter to 700 on the next tick, no raid; the units of the world rose with normal growth (344 to 376), no new bandit squad |
| frequency 1, same forced counter | `menu-s-191029` | same: counter 698 and falling, no raid in 15 game days |

Reading: a write of `raidingFrequency` or of `daysUntilNextRaid` in a running game does not start or stop a native raid within 15 game days; the game recomputes the counter. A real A/B for native raids needs a game year per run and was not done. For the mod AI, no change was seen for aggressiveness 0, 1 and 2, or for frequency 0 and 1.

## Not verified

- A native raid at a fixed frequency over a game year (settings are only read by the game at start, or the timer logic differs from a plain counter).
- AI Aggressiveness effect on mod-made vassal lords over a long run (claims, wars).
- Off Map Adversary Present: the baron preset was selected in the menu (`menu-q-191928`) but no new game was started.
- Each cell is one run. No spread was measured.
