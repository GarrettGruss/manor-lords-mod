# Question 3: Hussite raid with Off map adversary Absent and Raider frequency None

Fixture `playtest-noai` against the control `base` (Raider frequency Medium, a baron and 3 AI lords).
Evidence: `evidence/q3-base-raid-at-village.jpg`.

## Verdict

**The Hussite raid works in the playtest world. The game settings do not block it.** Spawn, composition, the lord army, the challenge, the leave rule and the region guard all pass. Two things differ from `base`, and neither comes from a game setting:

1. **The raid army goes to the region under the camera, not to the village.** The fixture saves the camera over a free region (`selbitz`). A forced raid there spawned and anchored its challenge at `Goldhof` (a free region 54 000 units from the village), although the mod log says `target=Nusslohe`. The army stood at Goldhof for the 25 game days and left by the time rule. With the camera moved to the village (`Nusslohe`), the challenge was over `Nusslohe` and the army stood at the village. The code path is the same in `base`, whose fixture camera was in the village. Cause: `lord_raid.start_checked` sends the lord to `battlefield_anchor({ lord })`, and that command uses the current region of the target pawn (the camera region). The camera also drifts by itself in a long run (cursor near the screen edge), so the region at the time of the spawn is not fixed. **This does not stop the plunder:** in a later control run (`menu-s-191029`, fixture `base`, camera region Goldhof, army at Goldhof about 60 000 units from the village) the plunder tick still took 68 goods a day (190 goods in 20 game days). The plunder is a mod rule that does not look at the army position. So the camera rule moves the army and the battle marker to a wrong place, but the village is still plundered. A mod finding for the owner (follow-up change), not a settings problem.
2. **Nothing to plunder.** In the playtest village the tier 1 stores hold 21 goods in total. The baron steal rule took all 21 on the first day (`steal wanted=100 taken=21`, then `taken=0`). The plunder tick then had nothing to take (`plunder wanted=64 taken=0` on every one of 21 days, camera in the village). In `base` the raiders took 54 goods per day at first (`looted_total` 156 after 18 game days). So the empty plunder comes from the small stocks of the owner's village, not from the settings.

## Scenario results

Same test scenarios on both fixtures (run ids are in the table). One run each: ranges are checked by the scenarios, not exact values.

| Test scenario | playtest-noai | base |
|---|---|---|
| `invasion-raid-composition` | pass, `q3-comp-noai-181016`: 3 squads, 100 units | pass, `q3r-comp-base-182942`: 3 squads, 100 units (the first base run `q3-raid-composition-base-181438` was a harness boot failure: slot did not appear in the save list; rerun passed) |
| `invasion-first-raid` | pass, `q3-first-raid-playtest-noai-181628`: plan 36 days, spawn on day 152 (plan day), 64 units | pass, `q3r-first-base-183129`: plan 15 days, spawn on day 220, 50 units (the first base run `q3-first-raid-base-182209` crashed during boot, before the scenario; rerun passed) |
| `raid-behavior-region-guard` | pass, `q3-behavior-region-guard-playtest-noai-182326` | pass, `q3-behavior-region-guard-base-182425` |
| `raid-behavior-lord-leave-reason` | pass, `q3-behavior-lord-leave-reason-playtest-noai-182529` | pass, `q3-behavior-lord-leave-reason-base-182735` |

The composition differs by random role pick (noai: `spearMilitia`, `mercenary_infantry`, `bowMilitia`; base: `spearMilitia`, `militiaFoot`, `brigandArchers`). That is the normal variation.

## Forced raid (commands `invasion_set_difficulty 1`, `invasion_plan_now`, `invasion_force_next`, speed 3)

| Run | Fixture | Camera region | Raid spawn | Challenge region | Result after about 20 game days |
|---|---|---|---|---|---|
| `noai-r-183429` | noai | selbitz (free) | day 116, 64 units, `target=Nusslohe` | Goldhof | stood at Goldhof, `plunder taken=0` (stores empty, see 2), left on day 141 (`reason=time`) |
| `noai-c-184435` | noai, camera moved to the village first | Nusslohe | day 116, 64 units | Nusslohe | army at the village, `plunder taken=0` (stores empty), still there on day 134 |
| `base-r-184008` | base | Nusslohe | day 205, 54 units | Nusslohe | army at the village, plunder 54, 54, 32, ... goods per day, `looted_total` 156 |

(A bandit camp had been spawned in `noai-r-183429` by a stray probe call before the raid. The raid did not use the bandit pawn: its units are owned by the mod's own lord "Hussite Raiders". The scenarios above ran with no bandit pawn and passed.)

## Mod code and game settings

- The Hussite raid is the army of a mod-made AI lord (`lord_raid.lua`: `spawn_ai_lord`, `lord_relations`, `lord_start_ai`, war, `spawnArmy`, `battlefield_anchor`). It needs no bandit pawn, no baron and no game AI lord. So Off map adversary Absent, AI opponents 0 and Raider frequency None do not stop it.
- Only `ManorCore.spawn_squads` (and the harness `spawn_units side=bandit`) need the bandit pawn. See `bandit-camps.md`.

## Not verified

- A full raid to the end in a village with stocks (plunder, burn, leave by loot) in the playtest world. Needs a village with goods.
- Whether the camera region rule matters to the owner's play: the army and the battle marker go to the region under the camera when the raid starts. The plunder is not affected (control run above), but the player sees the army in another place.
- One run per cell. No A/B repeat (the question was "does it work", not a rate).
