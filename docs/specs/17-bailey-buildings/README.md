# Spec 17: Buildings inside the manor bailey

Status: spike planned (2026-10-13). Issue: #68. Branch: `feat/17-bailey-buildings`. Criterion: M2 (spec 10), first explored in spec 12.

## Goal
The player can place normal buildings (burgage plots, industry) inside the manor bailey. Then the city can be walled in.

## Non-goals
- No pak change (no AES key is available).
- No change to the Keep limit (`maxInRegion`) or to storage (M1).
- No new walls (see spec 14).

## Background
- Spec 12: the bailey is the polygon of committed planner modules. The check that refuses buildings is in C++. Nine natives were hooked and gave zero events. Over a Keep, a normal building is refused. A bailey was never tested.
- Spec 14: the fixture `manor-bailey` has a manor, a gatehouse and a closed wall ring around an empty bailey.
- Spec 15: a burgage plot can be committed without the mouse (`plot_field_place`, `extractedPlots`, `addCommitFieldRequest`). The commit accepted plots in odd places.

## Plan
1. Spike A: with `manor-bailey`, place a normal building inside the ring with the OS mouse (`place_building`). Count buildings before and after.
2. Spike B: commit a burgage plot inside the ring with `plot_field_place` and `addCommitFieldRequest`. Count masters. Wait for builders. Check if the plot is built.
3. Spike C: control tests, the same actions outside the ring.
4. Spike D: if A or B is refused inside only, toggle reflected flags that the check might read.
5. If it works, write a named command and a scenario (COVERS M2). If not, write the findings into spec 12 notes and drop this spec.

## Open questions
- Q1: Is a normal building refused inside the bailey at all in this fixture?
- Q2: Does the plot commit skip the check that the mouse path uses?
- Q3: Do builders build a plot that was committed inside the bailey?
- Q4: Which reflected flag, if any, changes the result?

## Acceptance criteria
- [ ] Q1 to Q4 are answered with counts and run ids in `implementation-notes/`.
- [ ] Either a scenario (COVERS M2) passes 3 of 3 real runs, or the findings are folded into `docs/specs/12-manor-exploration/implementation-notes/bailey-buildings.md` and this folder is removed.
- [ ] No save function was called. The game is closed at the end.
