# M06 iteration 02: tribute-terms

Branch: `feat/M06-sack_and_terms-02-tribute-terms` (stacked on iteration 01, PR #180). Issue: #181.

## Goal
The invader offers terms while a lord raid is on the map (M00: a one-time payment, or vassalage with yearly tribute). Hostages are dropped (decision 8). Accepting ends the raid early through the M03.02 peace route. A paid-off raid does not sack the town.

## Design (UI later; a banner and named commands now, TBD)
1. Offer: when a lord raid spawns (`invasion.watch_spawn`, only a lord army) the mod opens an offer and shows a banner. Command `InvasionMod.terms_offer` opens one by hand (needs an active raid).
2. Amounts (TBD, `config.sack_and_terms.terms`): payment = `payment_base` x difficulty silver (100, 200, 300); yearly tribute = `tribute_base` x difficulty silver (30, 60, 90) every `tribute_days` (360) game days.
3. `InvasionMod.terms_accept kind=payment`: refused when the silver is below the amount. Otherwise the silver is paid, the offer closes, and the raid leaves with reason `terms` (`raid_behavior.force_leave`: same peace call and removal rules as every leave).
4. `InvasionMod.terms_accept kind=vassalage`: no payment now. The raid leaves with reason `terms`. State `vassal` is saved with the next tribute day. The tribute is collected by a scheduler job once the day is reached (the player pays what the silver allows, TBD; M08 will replace this with its own rule).
5. `InvasionMod.terms_decline` closes the offer. The raid goes on.
6. Not here (TBD): terms offered after a sack, the effect of vassalage on later raids (M02 plans one raid today), a UI.

## Changes
- `raid_behavior`: the leave start is one local function; new `force_leave(reason)` export.
- `features/sack_and_terms/terms_rules.lua` (pure), `terms.lua` (state, commands, tribute job). ModState keys: `terms_state` (0 none, 1 offered, 2 paid, 3 vassal), `terms_next_tribute_day`, `terms_paid_total`.
- Config `sack_and_terms.terms`.

## Acceptance criteria
- B1: amounts at difficulty 1, 2, 3: payment 100, 200, 300; tribute 30, 60, 90 (pure rules).
- B2: accepting a payment with enough silver lowers the silver by exactly the amount and the raid state becomes `left` with reason `terms` within 3 game days (peace removes the lord army). The village is not sacked (sack count 0 for this raid).
- B3: accepting a payment without enough silver is refused; nothing changes.
- B4: vassalage ends the raid the same way, costs 0 now, and sets `vassal` with the next tribute day = day + 360.
- B5: on the tribute day the silver falls by the tribute (or to 0 if less) and the next day moves 360 days on.
- B6: no crash; the village keeps people.

## Scenarios
- `sack-and-terms-pay-terms` (real game): small forced lord raid, `silver` set high by the base game cheat or read first; accept payment; check B2.
- Fake tests: `test_fakegame_sack_and_terms.py` (terms classes).

## Result
Not started.
