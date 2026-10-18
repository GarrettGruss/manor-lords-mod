# M07 iteration 04: loss-and-submission

Branch: `feat/M07-vassals-04-loss-and-submission` (stacked on PR #211, M07.03). Issue: #212.

## Goal
A vassal can be lost, and then it sends refugees (M09). A vassal with low loyalty submits to the invader: tribute stops. It can come back. (M00: a lost vassal cuts tribute and sends refugees; an unprotected vassal may submit.)

## Design (TBD values are marked)
- Loss: the slot is freed (region, lord, flags cleared, `vassals_lost` +1) and listeners get `{slot, region, families, reason}`. The refugees feature listens and sends a wave sized by `families` (M09.01). Banner "A vassal is lost".
- Detection: the poll compares the owner of a handed-over region with the pawn of its lord. A different owner means the vassal was taken (reason `taken`). Not seen in the real game yet: no invader takes a region in the harness.
- Test command `vassals_lose{slot}`: the loss path without a capture. The land after the loss (M00 question 8) is TBD. `loss_region = forget` (default): the lord keeps the land and goes independent. `take_by_lord`: another AI lord is given the region (an owner write). Both clearing the owner and `take_by_lord` crashed the game, see the result.
- Submission: at each season change, after the loyalty tick, a vassal at loyalty 10 or less submits: flag `vassal<N>_submitted`, the lord declares war on the player, the mod stops making peace for it, tribute stops (M08 skips it). A submitted vassal at loyalty 40 or more returns: the flag clears and the lord gets peace. Policy `light` and gifts raise loyalty, so the player can win it back.
- Not done: the vassal paying tribute to the invader (counted nowhere; only the flag exists).

## Changes
- `vassals`: loss, listeners (`on_lost`), `detect_losses`, `submission_tick`, keys `vassal<N>_submitted`, `vassals_lost`, `vassals_submissions`; rules `submission_action`; config `submission`, `loss_region`.
- `refugees`: listens to lost vassals. `tribute`: skips submitted vassals.
- Commands `vassals_lose`, `vassals_set_loss_region`, `vassals_submission_tick_now`.

## Acceptance criteria
- L1: a vassal at loyalty 5 submits (flag, counter).
- L2: the lord of a submitted vassal is at war with the player and the mod does not make peace.
- L3: a submitted vassal pays no tribute at a season change.
- L4, L5: at loyalty 45 the vassal returns and the lord is at peace again.
- L6: the lose command frees the slot; the land stays with its lord (`forget`).
- L7: the loss sends a refugee wave: +5 families at home, wave active.
- L8: 4 game days later the game runs, no crash.

## Scenarios
- `scenarios/vassals/loss_and_submission.py` (`vassals-loss-and-submission`), fixture base.

## Result
PASS in the real game (2026-10-18) with `loss_region = forget`. Notes: `../implementation-notes/iteration-04-loss-and-submission.md`.
- Runs `20261018-094318-80ce` and `20261018-094519-b470` pass (L1 to L8).
- Crashes with a region transfer after the loss: owner cleared, run `20261018-093104-446f` (0xd18); `take_by_lord`, run `20261018-093533-4f17` (0xffffffffffffffff). Both within seconds of the loss. The cause is not isolated (the lord AI loses its only region).
- Fake game tests: 8 new in `test_fakegame_vassals.py`, 1 each in the refugees and tribute tests.
