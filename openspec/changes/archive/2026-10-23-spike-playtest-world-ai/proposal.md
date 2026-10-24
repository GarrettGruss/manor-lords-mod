## Why

The owner's playtest world (issue #430) uses settings that may switch off parts of the Invasion Mod: AI opponents 0, Off map adversary Absent, Raider frequency None, Initial bandit camps 0, Random bandit camp spawn limit 0. In the playtest, the mod's bandit conversion failed with "no pawn for side bandit" (`mod/shared/HarnessBattle/HarnessBattle.lua:173` needs the game's bandit pawn to own spawned squads). We need to know what works in this world and what the player must enable in the game settings.

Issue: #430.

Related: #416 (`spike-scenario-template-menu`, question 3 covers the settings A/B), #424 (bandits order), #341 (`add-vassal-sack-wipe`, rebuild order).

## What changes

A spike on the fixture `playtest-noai` (copy of the owner's saveGame_34, see `notes/fixture.md`). No mod feature changes. Three questions:

1. **Bandit camps.** Can the mod create bandit camps in this world, or must the game settings (Initial bandit camps, spawn limit) enable them? Routes: find the bandit pawn or faction actor and check if it exists with camps 0; try to spawn a camp (`HarnessEncampment`, `HarnessBandits`) and a bandit squad; try to create the bandit pawn if it is missing.
2. **AI lord and construction.** Can a region be given to an AI lord, and does the AI lord then construct buildings? Routes: find AI lord pawns in this world; assign `region.ownerPawn` or call the game's claim function with an AI pawn; spawn or enable an AI lord if none exists; watch for construction sites over 10 to 20 game days. Prior work: #341, `docs/wiki/concepts/engine-limits.md` ("Ruins and the rebuild order").
3. **Hussite AI.** Does the mod's Hussite AI (features `invasion` and `raid_behavior`: spawn, march, plunder, leave) work with Off map adversary Absent and Raider frequency None? Run the existing raid test scenarios on the fixture, force a raid with named commands such as `invasion_plan_now`, and compare with the base fixture.

## Outcomes

- One note per question in `notes/`: what works, what fails, and the exact setting or call that decides it.
- Pictures of camps, construction sites and the raid in `evidence/`.
- A recommendation for the owner: which game settings the mod needs, and which parts the mod can do itself.
- Lasting engine facts go to the wiki before the archive.

## Impact

No living spec changes (`skip_specs: true`). No code changes except possible probes in the notes folder. Follow-up changes are proposed after the owner decision.
