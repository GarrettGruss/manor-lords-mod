# M07 iteration 03: policies-and-orders

Branch: `feat/M07-vassals-03-policies-and-orders` (stacked on PR #208, M06.03). Issue: #209.

## Goal
The player rules a vassal only through mod-owned policies and orders (M00). The game policy system is not used (`enactPolicy` returned false in 95 tries). Lua applies the effects.

## Design (TBD values are marked)
- Policy per vassal slot, ModState key `vassal<N>_policy`: `light`, `fair` (default), `heavy`. Config `vassals.policies`:
  - `light`: tribute factor 0.5, loyalty +3 at each season change.
  - `fair`: 1.0, 0.
  - `heavy`: 1.5, -5.
- Effects: the loyalty tick runs at each season change (saved last season `vassals_last_season`, the M04.02 pattern; no tick on the first poll). The M08 tribute share is multiplied by the factor of the policy.
- Order "send a gift": costs 50 silver, adds 10 loyalty (clamped to 100). Refused without silver or without a handed-over vassal.
- Commands: `vassals_set_policy{slot, policy}`, `vassals_order_gift{slot}`, `vassals_loyalty_tick_now` (test).
- No UI yet (a later widget, M12 style).

## Acceptance criteria
- P1: the default policy is fair.
- P2: fair keeps the loyalty at a season change.
- P3: heavy lowers the loyalty by 5 once per season change; light raises it by 3.
- P4: the tribute share is multiplied by 1.5 (heavy) or 0.5 (light).
- P5: a gift costs exactly 50 silver and adds 10 loyalty.
- P6: an unknown policy is refused; no crash.

## Scenarios
- `scenarios/vassals/policies_and_orders.py` (`vassals-policies-and-orders`), new game, season jumps.

## Result
PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-03-policies-and-orders.md`.
- `vassals-policies-and-orders`: runs `20261018-091740-fd3d` and `20261018-091941-2048` pass (P1 to P6).
- Fake game tests: 8 new in `test_fakegame_vassals.py`, 1 in `test_fakegame_tribute.py`.
- Flakes: run `20261018-091457-29b1` (the command poller of HarnessCommands died with a Lua IO error) and `20261018-091643-abc3` (access violation 0xffffffffffffffff after the handover) were not caused by the policy code; both happened before the first policy command.
