# Proposal: Remove vassal loyalty

Issue: #344.

## Why
Owner decision (chat, 2026-10-20), `openspec/changes/decide-open-mod-rules/design.md`, item 10: "For now the mod controls only the sacking of houses in an AI village. Any other effect on a region the player does not control goes through the review cycle (its own change). Tribute does not matter for AI regions. Vassal loyalty is not a mechanic: a vassal survives or dies. Whether a resource is really infinite in a vassal region does not matter, because Lua simulates the vassal tribute." The note in the same item says the existing loyalty effects (for example the law `trade_pacts`, effect `vassal_loyalty`) conflict with this answer and must be removed in a later change. This is that change.

## What Changes
Every loyalty effect found, and what happens to it:

| # | Where | Loyalty effect | Action |
|---|---|---|---|
| 1 | `mod/vassals` "Vassals live in a registry with loyalty" | Slot holds loyalty; `loyalty_start` 50; range 0 to 100 | Replace by a registry without loyalty |
| 2 | `mod/vassals` "Policies change tribute and loyalty" | `light` +3, `heavy` -5 at each season change | Policies change only the tribute factor |
| 3 | `mod/vassals` "The gift order raises loyalty" | `vassals_order_gift` costs 50 silver, adds 10 loyalty | Remove (open question 1) |
| 4 | `mod/vassals` "A vassal with low loyalty submits" | Submission at loyalty 10 or lower; return at 40 | Remove; a vassal survives or dies |
| 5 | `mod/vassals` "The feature offers named commands" | `vassals_set_loyalty`, `vassals_loyalty_tick_now`, `vassals_order_gift`, `vassals_submission_tick_now` | Remove these commands; state has no loyalty |
| 6 | `mod/tribute` "Vassals pay goods each season" | Share from 0.10 to 0.30 by loyalty | Fixed share (`tribute.share`, default 0.20, the value at loyalty 50) |
| 7 | `mod/tribute` "The vassal policy scales the tribute" | A submitted vassal pays nothing | Drop the submitted scenario |
| 8 | `mod/tribute` "Vassals also pay finite goods" | Scenario names loyalty 50 | Scenario without loyalty |
| 9 | `mod/tribute` "A raid on a vassal changes its loyalty" | Defended +5, undefended -15 | Remove |
| 10 | `mod/tech_tree` "Laws can be enacted and repealed" | Law `trade_pacts` effect `vassal_loyalty` +2; scenario checks loyalty | Remove the effect and the effect kind; the law keeps `tribute_share` +0.25 |
| 11 | `mod/finite_resources` "Vassals pay iron and salt as the permanent supply" | Text says the share follows loyalty; scenario names loyalty 50 | Share is fixed |
| 12 | Code and data | `tree.json`, `tech_tree/{init,rules,tree}.lua` (`vassal_loyalty_bonus`, effect kind `vassal_loyalty`), `vassals/*.lua`, `tribute/*.lua`, `config.lua` keys (`policies.*.loyalty`, `gift`, `submission`, `loyalty_start`, `share_min`, `share_max`, `protection`) | Remove |
| 13 | Tests and test scenarios | `test_fakegame_vassals.py`, `_tribute.py`, `_laws.py`, `_runlib_scenario.py`; `vassals/policies_and_orders.py`, `vassals/loss_and_submission.py`, `vassals/claim_without_victory.py`, `tribute/protection_and_loyalty.py`, `tribute/tribute_payout.py`, `tech_tree/laws.py`, `finite_resources/vassal_supply.py` | Update or remove |
| 14 | Docs | Loyalty text in `design/mod/invasion-mod.md` and `design/mod/decisions.md` (owned by the owner), `docs/wiki/architecture/invasion-features.md`, `CHANGELOG.md` files, the Purpose lines of `mod/vassals`, `mod/tribute` | Wiki and Purpose lines are updated here. The `design/` files are not changed by this change; the owner decides (open question 3) |

A vassal now survives or dies. A vassal dies by a siege (`mod/tribute`) or by a capture (`taken`).

## Non-goals
- The vassal sack wipe and the restore. The change `add-vassal-sack-wipe` (#341) does that.
- The tribute rules for goods, seasons and policy factors, other than the loyalty part.
- A new way to keep a vassal safe or to make it submit.

## Design pillars
Pillar 2 (rule through others: vassals only by policies and orders) stays: the policies remain and change the tribute factor. The change removes one lever (loyalty); it adds no new effect on an AI region (owner, item 10).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/vassals`: registry, policies and commands without loyalty. REMOVED: the gift order, the submission.
- `mod/tribute`: fixed share. REMOVED: the loyalty change after a raid.
- `mod/tech_tree`: "Laws can be enacted and repealed" scenario for Trade Pacts without loyalty.
- `mod/finite_resources`: "Vassals pay iron and salt as the permanent supply" without loyalty.

## Impact
- Code and data: see row 12. Save compatibility: old saves hold `loyalty` and `submitted` fields in the vassal registry. The mod must ignore them (decided in the spike task 1.1).
- Overlap: `add-vassal-sack-wipe` (#341) also changes the requirement "The feature offers named commands" of `mod/vassals`. Merge one first and rebase the other.
- Real game runs, one at a time.
