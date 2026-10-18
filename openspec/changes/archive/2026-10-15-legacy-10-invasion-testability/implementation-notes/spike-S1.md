# Spike S1: raid timer

Date: 2026-10-10. Runs (in `runs/`, not in git): probe-s1-d, probe-s1b-a, chk-raid-timer, series of `raid-timer` (3 of 3 pass).

## Question
Can the harness read and write the raid timer, does the write hold, and what arrives when the timer reaches 0?

## Method
Probe scenario `probe-raids` (groups s1, s1b) and the helper command `raid_state` (mod/shared/HarnessRaids). Reads and writes go through the bridge (`TemporalComponent`). Units are counted with `units_census` (spike S3).

## Where the raid state lives (jmap, `Binaries/Win64/ue4ss/*.jmap`)
| Name | Owner | Type | Read in game |
|---|---|---|---|
| `daysUntilNextRaid`, `daysSinceLastRaid`, `lastBanditCampSpawnedDay` | `TemporalComponent` (also `MLSaveGame`) | Int | yes, and written |
| `defaultRaidIDs`, `eliteRaidIDs` | `RaidSettings` (a `DeveloperSettings` class, CDO `/Script/ManorLords.Default__RaidSettings`) | Array of Name | read: default `["Brigands"]`, elite `["Brigands","brigandPolearms"]`. Not written |
| `yearsUntilFirstRaid`, `raidingFrequency`, `maxBanditCamps`, `initialBanditCamps`, `AI_aggressiveness` | `GameSetupParameters` (in `MLGameInstance.gameSetup.currentGameSetup`) | Byte | read: 2, 2, 3, 1, 1 in the test save. Not written |
| `bCanRaid`, `lootValue` | `SavedSquad` (save file struct only) | Bool, Int | not reachable live |
| `daysUntilRaid` | parameter of `PawnCPP:issueRaiderTrackingQuestIfNew` | Int | n/a (a function parameter, no state) |
| `HasRaiders` | parameter of a game setup menu function | Bool | n/a |
| `spawnRaiderForce` | field of the quest `Reward` struct | Int | n/a (it is a reward field, not a function) |

Do not read `MLGameInstance.gameSetup` as a whole through the bridge: the struct holds a soft object (`Thumbnail`). The helper reads only the byte fields.

## Results
- Start of the test save: `daysUntilNextRaid` 730 (= `yearsUntilFirstRaid` 2 x 365), `daysSinceLastRaid` 0, `lastBanditCampSpawnedDay` -1. Day 61, spring, year 1.
- Write: 730 -> 50 and 0 -> 10 read back at once. After 6 game seconds still 50 and 10. The write holds; the game does not recompute it.
- Countdown: after 1 game day 49 and 11. Each day tick: until -1, since +1.
- Raid on timer 3 (set at game day 0): after day 1 -> 2, day 2 -> 1, day 3 -> 208. The raid appeared on the 3rd day tick (the tick that brings it to 0). Timer 1 (probe-s1-d): the raid appeared on the 1st tick, new timer 353. So a timer N gives a raid N day ticks later. New timer after a raid: 353 and 208 (random, not a fixed number).
- On the raid tick `daysSinceLastRaid` is 0 and the player `log` list grows by 2 (1 -> 3). `InBox` (0), `outbox` (0) and `quests` (0) did not change at the announcement or at the arrival.
- What arrives: bandit side 18 -> 36 units, one new squad of 18 units, `Soldier` role. Seen at a far region (Krumme Leite, x -80053, y 27402), not at the player region (Hochweg, x about 40000, y -78000). It walked: x -80053 -> -57463 in one game day, then -58023 (almost stopped). In the test run the units carried loot 53 total (max 4) one day later, 69 (max 5) two days later: raiders loot on their own.
- `run_game_days(1)` sometimes advances 2 days (daysTotal 3 -> 5): read the day count, do not assume 1.
- Another effect (probe-s1-b): an `InBox` letter arrived on day 6 and two AI squads showed up. Not related to the raid timer as far as seen (not analysed).

## What works
`set_raid_timer(days_until, days_since)` action (read back verified), `raid_state` command, arrival detection by the bandit count. Scenario `raid-timer` (3 of 3): timer 2 -> a squad of 18 within 2 to 3 days, new timer 30..800, `daysSinceLastRaid` 0.

## What does not work or is unknown
- No announcement in the base game: no letter, no quest, no alert was seen before the raid. T1 needs the mod to announce. How a raid is "announced" in the UI is not verified (S9).
- The raid ID lists and the setup bytes were read, never written. Whether a changed list changes the composition is not tested.
- Timer 0 written directly (probe-s1-d, last step): the game process was ended (exit code 15) while the run continued. This looks like an outside kill (it also happened twice at boot of other runs), not a proof of a crash. Not verified. Use 1 or more.
- Season rules (T5) are not seen: the timer is random after the first raid.

## Verdict
partial. Method verified: `ctx.actions.set_raid_timer(n)` + `run_game_days` + `units_census` (raid-timer). Not verified: announcement, season rule, writing the raid lists.
