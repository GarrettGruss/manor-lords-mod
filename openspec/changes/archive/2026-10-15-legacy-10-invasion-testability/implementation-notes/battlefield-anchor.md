# Battlefield anchor (issue #99)

Date: 2026-10-15. Lead: `openspec/changes/archive/2026-10-15-legacy-13-mod-inspection/implementation-notes/better-battlefield.md`. The code is our own: module `mod/shared/HarnessBattlefield`, command `battlefield_anchor` (HarnessActions version 49).

## Result
**Verified in the real game: the anchor moves the battle site of a challenge to the manor.** On fixture `base` (region Nusslohe, 21 `battlefield_BP_C` actors):

| Arm | Runs | `Challenge.Center` distance to the manor |
|---|---|---|
| anchor (manor) | 7 (smoke run + 6 suite runs) | 757 to 760 units (the center is the manor plus a small offset) |
| control (plain `lord_challenge`) | 1 launch, 4 challenges | 46 853 units, every time |

In the control arm the game picked `battlefield_BP18` at (-17065, -24729), and it picked the same actor for 4 challenges of 4 different lords over the same region. So the pick is not random for one region: it looks like a fixed choice. In the anchor arm `Challenge.Battlefield` is the first actor (`battlefield_BP10`) and its position at that moment is the anchor.

## What the command does
`battlefield_anchor` (HarnessBattlefield):
1. Finds all `battlefield_BP_C` actors, saves their positions.
2. Moves them to the anchor with `K2_SetActorLocation`. The anchor is `x`,`y`, or the manor of the region named `region` (object name), or the manor of the region of `target` (default 0, the player). If the region has no manor, the village center, then the region actor.
3. If `lord` is set, it calls `lord_challenge` in the same step. This avoids a timing race between two commands.
4. Puts the actors back after `delay_ms` (default 500, 0 to 30000) with `ExecuteWithDelay`. A second anchor is refused while one is active.

`battlefield_state` is read only: it lists the actor positions, the last restore (`restored`, `failed`) and the anchor that the same request would use (`would_anchor`). `lords_state` now also gives, for each challenge, `center`, `battlefield` and `battlefield_at` (the actor position now).

## Facts from the real game
- `Challenge.Center` is a Vector and it is readable. At creation it is equal to the position of `Challenge.Battlefield`. After a few seconds (status 2, combat) the center moved by about 500 units.
- All 21 actors were moved and restored in every run (`last_restore` restored 21, failed 0). `Challenge.Battlefield` keeps the object, so after the restore its actor position is the home position again. Use `Center`, not `battlefield_at`, after the restore.
- `Region.manor` (lowercase) works. The manor of region Nusslohe stands at (-43956, -63097).
- A second and third challenge over the same region are allowed. They share the battlefield of the first one in the control arm.
- The lord army (`SMUnit.realPos`): the anchor arm army was 15 744 units from the manor 5 s after the challenge; in the control run all lord squads were gone at the first read (the lord's army was killed or never counted), so the army distance is not a usable metric here. The battle position itself is `Center`.

## Test method note
The first suite run was invalid. `run.py --env` and suite variant `env` go to the GAME process. A Python scenario cannot read them with `os.environ`. All 6 suite runs ran the anchor arm (`anchor_arm` was 1 in the control runs). Fix: read variant options with `ctx.variant_option(name, default)`. The same trap exists in older probes that read `os.environ` (for example `probe-lord-village` with suite `lord-village-ab`): their variants may not have taken effect. Check before you rely on those A/B results.
The launch cap (8) was then too small for 3 more control runs. One control launch was made with `BATTLEFIELD_EXTRA_LORDS=3`, which adds more lords that challenge the same region. The 4 samples are not independent (same actor every time), so the statistics tool is not meaningful. The difference (757 against 46 853) is far outside any noise seen in 7 anchor samples.

Suite file: `harness/suites/battlefield-anchor-ab.json` (3 control, 3 anchor). Run it again after the fix to get the formal verdict.

## Bandit raids and challenges (task 3)
Not measured in the game: the launch cap was spent on the A/B. Evidence so far:
- Spike S1 and the raid notes never show a challenge for a raid. `lords_state` was not read during a raid before.
- A raid is made by `spawnRaiders` for the bandit pawn. The harness spawns it directly (`rebel_raid_rally`), no `initChallenge` call is involved.
- The challenge list was empty in every `lords_state` read before a `lord_challenge` call (`challenges_before` was 0 in all runs).
So raids very likely create no challenge, and the anchor lever works for AI lord challenges only. Hidden probe `probe-raid-challenge` is ready: it starts a real raid and records `challenges` four times. Run it once (about 4 minutes) to close this point.

## Open
- Run suite `battlefield-anchor-ab` again (6 launches) for the formal A/B verdict, with `ctx.variant_option` in place.
- Does the lord army walk to the anchor? Needs a longer watch with a stable army (the army died in the control run).
- Test with a player manor that is built (this fixture region has a manor object; the anchor kind was `manor`).
