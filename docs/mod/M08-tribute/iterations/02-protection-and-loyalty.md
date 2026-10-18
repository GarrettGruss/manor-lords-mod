# M08 iteration 02: protection-and-loyalty

Branch: `feat/M08-tribute-02-protection-and-loyalty`. Issue: #214.

## Goal
A vassal expects protection. A raid on a vassal region that the player does not defend lowers its loyalty. A defended raid raises it. Low loyalty lowers the tribute (iteration 01 share formula) and, at loyalty 10 or less, the vassal submits (M07.04).

## Design (TBD values are marked)
- A raid has a target region (`info.target.region` from the invasion feature). The raid tracker (M03) stores it as `raid.target`.
- The tracker gets an end watcher: `raid_behavior.watch_end(fn)`. It runs once when a raid is no longer active, with the raid summary (state, leave reason, target).
- Outcome of a raid on a vassal region (TBD simple rule):
  - defended: the raid state is `destroyed`, or the leave reason is `losses` (the player killed enough raiders);
  - undefended: any other end (leave reason `loot` or `time`, or raiders that left by themselves).
- Loyalty change (TBD): defended +5, undefended -15. Config `tribute.protection`.
- A raid whose target is not a vassal region (the home region) changes nothing.
- The loyalty change uses `vassals.set_loyalty` (clamped 0 to 100). The season tick of M07.04 decides the submission.
- The tribute share of iteration 01 already grows with loyalty, so lower loyalty gives less tribute.
- State: ModState keys `protection_defended`, `protection_failed` (counts).

## Changes
- `raid_behavior`: `raid.target`, `watch_end`, `target` in the summary.
- `tribute`: `protection.lua` (hook) and pure rules in `rules.lua`. Command `tribute_test_raid_result` (harness test: feeds the same handler with a raid result for a slot).
- Config `tribute.protection`.

## Acceptance criteria
- P1: an undefended raid on a vassal region lowers its loyalty from 50 to 35.
- P2: a defended raid on a vassal region raises it from 50 to 55.
- P3: a raid on the home region changes no loyalty.
- P4: three undefended raids bring loyalty to 10 or less; the next season change makes the vassal submit and tribute stops.
- P5: loyalty stays between 0 and 100.
- P6: no crash in the run.

## Scenarios
- `scenarios/tribute/protection_and_loyalty.py` (`tribute-protection-and-loyalty`).
- The raid-end plumbing (target, watcher) is covered by fake game tests. The real-game scenario feeds raid results through the test command, because a raid does not yet target a vassal region (iteration M02.03 follow-up).

## Result
not started
