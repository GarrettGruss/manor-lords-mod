# Spec 32: Manor Wagenburg (spike)

Status: spike done (2026-10-18). Issue: #233. Branch: `feat/32-manor-wagenburg`.

## Goal
Find out if the manor system can be used to build a Wagenburg camp.
Wagon models replace the manor wall (palisade) pieces. A large tent replaces the keep.
The camp then reuses the manor wall collision and pathing: units cannot walk through the wall, the gate works, and defenders hold the wall.

## Non-goals
- A release of generated assets (the Meshy license check is open, spec 21).
- Animation, siege rules, balance.
- New native code. The spike uses data (pak) and named commands only.
- Camps owned by the AI (only a note on what it needs).

## Plan
1. Research the data model: wall piece, gate, tower and keep (rows, Blueprints, meshes), and where the collision comes from.
   Earlier notes (spec 14) say the block is native obstacle data (`Obstacle2D`), not the mesh. If true, a mesh swap keeps the block.
2. Make assets: one wagon mesh (Meshy via `genmesh.py`, spec 21 and 30 method) and a large tent (an existing tent mesh or Meshy).
3. Pak: replace the wall piece mesh with the wagon, and the keep with the tent. Keep the original data for collision.
4. Game: use fixture `manor-bailey` (a built manor with a palisade ring and a gate) or build one without the mouse.
   Check that wagons show on the wall line, that the tent shows as the keep, and that there is no crash.
5. Pathing: spawn enemy units outside, bait inside. Compare the unit positions (`SMUnit.realPos`) with and without the pak.
6. Notes per topic in `implementation-notes/`, and a recommendation.

## Result (2026-10-18)
- The manor can be reskinned. A pak that replaces the wall piece mesh (`SM_MERGED_C_SG_PalisadeWallNarrow_Ubeam`) by a Meshy wagon shows 56 wagons on the ring. A second pak that replaces the keep mesh (`SM_MERGED_C_SG_Manor_MainTower_Lv1_New`) by a Meshy tent builds a tent keep (garrison 24). Notes: `implementation-notes/replacement-test.md`, `meshy-assets.md` (60 credits).
- The collision is the native obstacle list that a built wall piece adds, not the mesh. The wagon ring read the same 337 obstacles. Bandits (18, 4 runs) entered by the gate, with and without the pak, with no wall crossing. Notes: `data-model.md`, `pathing-test.md`.
- The swap is global (every manor). A separate enemy camp is not possible this way. Notes: `implementation-notes/invasion-recommendation.md`.
- Runs `s32-1` to `s32-11` (git-ignored `runs/`). New: command `mesh_actors` (HarnessActions 58), probe `probe-manor-wagenburg`, tool `s32_track_report.py`, paks `s32wall_P.pak`, `s32keep_P.pak`.

## Open questions (original, answered above unless marked open)
- Which asset does the built wall piece read: the mesh asset, the Blueprint, or a data row? Answer: the mesh asset through `BM_SG_Manor_Wall_Lv1` (`MainBld_470`); a swap by path works.
- Does a bigger or different mesh change the obstacle footprint (is it read from the mesh)? Answer: no (337 obstacles, same paths).
- Can the keep look be changed without the mouse and without a crash? Answer: yes (mesh swap, `manor_blueprint_add` flow).
- Does the AI or an invasion need its own manor for a separate camp? Open: probably yes; an AI manor with a wall was not studied.

## Acceptance criteria
- [x] A note records the data model of wall, gate, tower and keep, and where the collision comes from.
- [x] A note records which replacements worked (wall mesh, keep), with run ids and screenshots.
- [x] A note records the pathing result with and without the pak (run ids, unit positions).
- [x] A recommendation for the Invasion Mod: use, cost and risks.
- [x] No AES key in git (diff grep before each commit). Meshy credits are recorded.
