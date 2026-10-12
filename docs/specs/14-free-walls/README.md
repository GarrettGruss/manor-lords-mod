# Spec 14: Walls outside the manor system

Status: spike done for Q1, Q2, Q4, Q5; Q3 and Q6 open (2026-10-11). See `implementation-notes/free-walls.md`.

## Goal
Find out whether the player (or the mod) can build defensive walls that are not part of the manor (castle planner), so a whole town can be
walled in while the manor bailey stays small. If yes, this meets the defense goal of criterion M2 (spec 10, spec 12) another way: the
soft-lock of building inside a large bailey is avoided, because the bailey does not have to cover the town.

## Why
- Spec 12: inside the manor area normal buildings are refused (reported by the user; the developers said a source rule prevents a fix).
  The bailey area could not be tested before; the fixture `manor-bailey` (spec 06, part D) now has one.
- Walls are not manor modules. The 3 bailey walls of `manor-bailey` are `Road` objects with `wallType` 2 (Wooden); EWallType has
  None, Fence, Wooden, StoneLow, StoneHigh. While the user drew them, the pawn had `roadmode` and `wallMode` on.
- The player pawn has `switchWallMode`, `joinWalls`, `findNearestWallSnapPoint`, `ReverseSelectedWall`, `wallCursor`, `splitWallsByCastleModule`.
- The DataTable `buildingStats` has rows `WoodenWallPiece` (470) and `WoodenPlatform` (471) next to the manor rows (`Manor_Walls` 50,
  `Manor_Wall_Stone_Small` 476, `Manor_Wall_Stone_Large` 477).

## Non-goals
- New wall meshes or assets.
- Fixing the inside-bailey rule itself (that is spec 12, M2).
- Calling any save function. Changing the user's saves.

## Questions
- Q1: Can wall mode be used outside the castle planner (no manor selected)? What does the game do: a wall `Road`, a construction site, nothing?
- Q2: Does a free wall need goods and builders, and do builders finish it? What does it cost?
- Q3: Does a free wall block units (raiders path around it, or attack it)? Is there a gate?
- Q4: Can normal buildings be placed next to and inside a ring of free walls?
- Q5: Can the wall tool be offered to the player without the planner (a menu entry, a key, the `WoodenWallPiece` row, a building category)?
- Q6: Does a free wall survive a save and load? (Only if Q1 works; a save needs the user, as for `manor-bailey`.)

## Plan
1. Read the wall data of `manor-bailey`: the wall `Road` objects (points, `wallType`, `isBlueprint`, any owner or manor link), the pawn's wall
   functions and their parameters (jmap), and the building rows 50, 470, 471, 476, 477 in `buildingStats`.
2. In a game without a manor (`base` or a new game): turn on the road tool and wall mode by call (`setRoadMode`, `switchWallMode`), draw a short
   wall with the real mouse (spec 07 real-mouse input), commit it (`commitRoad`), and read what was made. Time-box.
3. If a wall exists: run game days at 8x and check construction; spawn a small raider group on the far side and watch paths (`realPos`).
4. Check Q4 with `place_building` (real mouse) next to and inside the wall ring.
5. Look for a way to offer the tool (Q5).
6. Write the findings to `implementation-notes/free-walls.md`. Turn each working primitive into a named command (HarnessActions) with a fake
   game test; a scenario only when a criterion needs it.

## Open questions
- Is wall mode only reachable through the planner widget? If the C++ rejects a wall without a manor, is there a flag or data value to allow it?

## Acceptance criteria
- [x] `free-walls.md` answers Q1 to Q5 with evidence (calls, values, screenshots), or with "not possible, because" and the evidence.
- [x] If a free wall can be built: a named command creates it (no raw eval), and a read command counts wall segments and their state.
- [ ] If a free wall can be built: builders finish it, and units are blocked by it (raider positions before and after).
- [x] No game asset, key or save data is in git. No save function was called.
