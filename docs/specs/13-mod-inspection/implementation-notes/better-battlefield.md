# BetterBattlefieldMod v2.3 (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\BetterBattlefieldMod-306-1-3-1775710991` (Nexus file id 306; the number 1775710991 is a Unix time, 2026-04-09). Nothing was run.
Files: `BetterBattlefieldMod/Enabled.txt` (0 bytes), `BetterBattlefieldMod/Scripts/main.lua` (10285 bytes, 275 lines). No README, no author, no license text. Archive: `BetterBattlefieldMod-306-1-3-1775710991.zip`, 3494 bytes, SHA-256 `56654178f64d5c2180be221e77f220b0f256dfa98c871b3c705cc294642bad6b`. English comments.

## What it does for the player
When a claim challenge starts, the battle circle is placed at the defender's manor (or at the region centre if there is no manor) instead of a random pre-placed spot. (main.lua:1-12)

## How it works
- One hook: `RegisterHook("/Script/ManorLords.RTSMultiEngineCPP:initChallenge", OnInitChallengePre, Noop)` (main.lua:260-266). The callback gets `(ctx, challengedPawn, challengedBy, Region)`; the mod uses the third argument as the defender region (`a2`, main.lua:248-255).
- It reads the region position from `RootComponent.RelativeLocation` and the manor position from `region.Manor` (main.lua:113-154). `MANOR_WEIGHT` 1.0 means the manor itself (main.lua:18).
- It finds ALL actors of class `battlefield_BP_C` with `FindAllOf`, saves their positions, moves every one to the anchor with `K2_SetActorLocation(bf, {X,Y,Z}, false, {}, true)` (main.lua:159-163, 194-223).
- After `RESTORE_DELAY_MS` = 500 ms (`ExecuteWithDelay`) it moves them all back (main.lua:22, 226-236). Reason: the game picks "whichever" battlefield actor at the time of `initChallenge`, and has "assigned and rendered" it after 500 ms. So the challenge keeps the moved position while the map actors return home.
- It is a pre-hook; it does not change the return.

## Game version and signs it is stale
No game version is written. File date 2026-04-09, so it was made against an older 0.8.x. Against the 0.8.111 jmap:
- Present: `RTSMultiEngineCPP:initChallenge(challengedPawn: PawnCPP, challengedBy: PawnCPP, Region: Region)` (the mod's `a2` is the third argument = Region, so the argument order still fits), class `/Game/CPP_BP/battlefield_BP.battlefield_BP_C` (parent `/Script/ManorLords.Battlefield`, one property `masterPtr`), `Challenge.Battlefield` (an object reference), `Challenge.Center` (Vector), `Region.manor` (SMBuildingMaster) and `Region.townCenter`.
- Name case: the mod reads `region.Manor`; the jmap property is `manor`. UE4SS name lookup should be case-insensitive (FName), but this is not verified.
- The comment says "attacker's region / defender's region" for the two arguments; in 0.8.111 these are pawns and a region. Code works only because it takes the third argument.
- Verdict: names fit 0.8.111. Behavior not tested.

## Risk review
Pure Lua, no file or network access. It moves map actors for 500 ms; if the restore callback is lost (for example a load during that time) the circles stay at the manor. It uses `pcall` around everything and logs with `print`. License: none given.

## Lessons for us
- **Place of battle**: the battle site of a challenge is a `Battlefield` actor chosen inside `initChallenge`. Moving all actors before the call changes where the battle happens. For an invasion mod this is a clean way to pull the fight to a village or to a place that is good for tests, without any squad order. The `Challenge` struct also has `Center`.
- Squad steering: still none. This is an indirect lever, in line with S11 (steer inputs, not squads).
- Timing: a hook on `initChallenge` fires before the challenge exists. Our `lord_challenge` command (HarnessLords) calls the same function, so the same hook runs for our invaders.
- Raids: bandit raids use no challenge in what S1 saw, so this lever works for AI lord challenges (the baron, new lords), not for the timer raid. Unverified.

## Test idea for the harness
Scenario `battlefield-anchor`: with the mod installed (stand-in copy of the idea, not this file), run `lord_challenge` twice, once with a stand-in that moves all `battlefield_BP_C` to the player's manor and once without. Read `Challenge.Center` and the distance of the lord's army hold position to the manor (`SMUnit.realPos`). Assert, with ranges, that the distance is smaller with the move (A/B, 3 runs each).
