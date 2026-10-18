# Spec 30: Wagenburg encampment (spike)

Status: spike done (2026-10-18). Issue: #229. Branch: `feat/30-wagenburg-encampment`.

## Goal
Find out if a Wagenburg (Hussite war wagon fort, a ring of wagons) can be made with Meshy and shown in the game as a military encampment.
The encampment should replace the bandit camps the game spawns, or be spawned by the mod in neutral or AI-owned territory.

## Non-goals
- Animation, siege rules, or garrison logic.
- Balance.
- A release of the generated asset (the Meshy license check is still open, spec 21).
- Work on war wagon units (spec 29 part B does that). This spec only reads its notes.

## Plan
1. Model: make one Wagenburg mesh with `genmesh.py` (spec 21 method). If no key or no network, record it and use a placeholder.
2. Convert: import in UE 5.5.4 headless, make a `BM_` class, cook, pak (spec 18 and 21 method).
3. Hosts to test:
   - (a) replace the mesh of the bandit camp class (row 100). Bandits must still use the camp.
   - (b) a new building row (test id, spec 23 range rule) placed by Lua.
   - (c) a static mesh actor spawned by Lua in neutral or AI territory.
4. Spawning: spawn the encampment in neutral and AI-owned territory by named commands (no eval). Test if the game's bandit camp spawn can be redirected to it.
5. Notes in `implementation-notes/`, one file per topic. Recommendation for the Invasion Mod: which host, what it costs to ship.

## Result (2026-10-18)
- Meshy made a usable Wagenburg on the first try (30 credits, 11354 vertices, 14.6 m ring). Look: light grey, not brown (open). Note `implementation-notes/meshy-model.md`.
- Host a (row 100 retargeted to the new Blueprint): WORKS. The game's bandit camp spawn gives a camp with the Wagenburg mesh; bandit counts equal the control. Runs `s30-2`, `s30-3`, control `s30-4`.
- Host b (new row 4000 placed by the player): the row loads; placement needs the mouse and was not run (open). Proven for other new ids in spec 18 and 21.
- Host c (plain actor spawned by Lua): WORKS in neutral and AI-owned regions. It is not saved by the game and has no game logic.
- Details: `implementation-notes/host-tests.md`. Recommendation: `implementation-notes/invasion-recommendation.md`.

## Open questions (original, answered above unless marked open)
- Does a Meshy model of a ring of wagons come out as one usable mesh at game scale?
- Does the camp class keep working when its mesh is replaced?
- Which host survives save and load, and AI ownership?
- Can the bandit camp spawn be redirected without native code?

## Acceptance criteria
- [x] A note records the Meshy result (model made or not, credits).
- [x] The mesh shows in the game in a harness screenshot, or the blocker is recorded.
- [x] A verdict (works / partly / blocked, with run ids) for each host a, b and c. (b is partly: no mouse run.)
- [x] A verdict for spawning in neutral and AI territory, and for redirecting the bandit camp spawn.
- [x] A recommendation with the ship cost.
- [x] No key in git (diff grep before each commit).
