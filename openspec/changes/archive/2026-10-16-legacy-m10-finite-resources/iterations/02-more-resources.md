# M10 iteration 02: more-resources

Branch: `feat/M10-finite_resources-02-more-resources` (stacked on M10.01, PR #225). Issue: #226.

## Goal
Salt and clay are finite home deposits too. Vassals pay iron and salt as the permanent supply.

## Changes
- Config `finite_resources.resources`: `salt` (good 145, size 300) and `clay` (good 146, size 500), TBD. Same counter and limit lever as iron.
- Config `tribute.finite_goods`: iron 10 and salt 6 units per family. The tribute pays them next to the main goods with the same share (loyalty, vassal policy, laws). Result `finite` per payment and `finite_paid` in `tribute_state`. `paid_total` still counts the main goods only.
- Tribute goods are not production, so they do not reduce the home deposits.

## Acceptance criteria
- V1: one vassal (5 families, loyalty 50) pays 10 iron and 6 salt. V2: the home stores rise by that. V3: no failed deposit. V4: the home deposits stay full.
- Fake game: three deposits, an empty salt deposit limits only salt, tribute pays iron and salt, the policy scales them.

## Result
PASS in the real game (2026-10-18), `--new-game`. Runs `20261018-104632-be77` and `20261018-104731-d2a9` pass (V0 to V4). `finite-resources-iron` still passes with three deposits.
Open: clay has no vassal supply (TBD: not named in M00); size and rates are guesses until the use rate is measured.
