# Policy follow-ups (issue #60)

Date: 2026-10-12. Fixture `base` (region Nusslohe, 35 people, level 1). 7 game launches, all closed, no crash. No save function was called.
Probe: hidden scenario `probe-policy-followups` (modes `census`, `enact`, `enact2`, `ab`, `click`, `aba`). Report tool: `harness/tools/policy_ab_report.py`.
Run folders (git-ignored): `pf-census`, `pf-enact`, `pf-enact2`, `pf-enact3`, `pf-ab-short-off`, `pf-ab-short-on`, `pf-click`, `pf-aba`.

## 1. Strict fasting (policy 12) during a food shortage

Question: does signing policy 12 change food use or approval?

Method:
- Shortage: the base village has no berries, bread or vegetables in stock. The probe gave 6 each of goods 171, 172 and 230 (18 units).
  Normal stock was not run (launch limit).
- Run 1 and 2 (A/B, two games, 6 game days each at 3x): policy unsigned, and policy signed with `policy_sign`.
- Run 3 (`aba`, one game): 8 days unsigned, 8 days signed, 8 days unsigned.
- Read each game day: approval, approval factors, food stock (goods 171, 172, 230), `supplies_food`, population.

Numbers:
- Food stock: 18 at the start. In both A/B games it was 18, 18, 18, 18, 18, 17, 17 on days 0 to 6 (identical, signed or not).
  In the `aba` game it was 18 before, 17 in all of the signed block and 17 in the last unsigned block (one unit lost on day 5, before the policy).
- Approval, unsigned and signed games: 71, 71, 72, 73, 73, 74, 75 in both. Identical.
- Approval in the `aba` game: 71 to 75 (A1), 73 to 75 (B), 75 to 76 (A2). One dip of 2 points one day after signing (75 to 73), back to 75 by day 3 of the block.
  The population grew from 35 to 38 in the same days (new arrivals), so the dip is not proven to come from the policy. It was seen once.
- No new approval factor (no `hardship`, no `hunger`, no `starvation`) in any run. The factor names stayed `SatisfiedAmenities`, `SatisfiedMarketCommodities`, `foodVarietyGood`.
- `Region:hasPolicy(12)` still false while 12 is in `policiesSigned` (as in the first spike).

Verdict:
- The test has no power. The village used about 1 unit of the 18 in 24 game days, signed or not. A policy that skips every 5th meal cannot show in a number that does not move.
  The families seem to eat from other sources (market stalls, own gardens), not from the counted stock.
- Range assertions that hold in this village: approval stays within 71 to 76 and rises by at most 5 over 8 days, signed or unsigned. Food stock changes by at most 1 unit in 8 days, signed or unsigned.
- Not shown: any effect of signing on food use or approval. Not excluded either. Open: a village with real food use (farms, a market with food, more people), a longer run, and a read of `GetFamilyConsumptionData` (returns structs by value, not safe to call).
- A signed policy 12 gives no effect that Lua can see now. A mod-owned ration edict needs its own effect, as the first spike said.

## 2. Why `PawnCPP:enactPolicy` returns false

Tried (all returned false, nothing changed, no crash):
- Slots -1, 0, 1, 2, 3 and policy ids 0 to 18 (95 calls, command `policy_enact_sweep`, unsafe, `HARNESS_ALLOW_UNSAFE=1`). None returned true. Slots 1 and above are outside `getMaxPolicies` (1).
- `PawnCPP.availablePolicies` written with [2, 4, 7, 8, 10, 12], then enact 12 slot 0: false.
- Silver and influence raised to 5000: false (so not a silver or influence cost).
- Settlement level set to 2 (`getMaxPolicies` stayed 1): false.
- Development points spent are 0 in the base village. Not changed (no known writer). Not excluded as the cause.
- The bridge cannot pass object arguments (`Value must be UObject or nil`), so the call must go through a named mod command.
- The functions on the pawn and region about policies: `enactPolicy` (PawnCPP), `setPolicySigned`, `hasPolicy`, `getNumDevPointsSpent`, `getMaxPolicies`, `getAllAvailablePolicies` (Region). `props` with the pattern "polic|point" found no more members (the pattern filter returned an empty list; names of properties already known: `Region.policies`, `Region.policiesSigned`).
- A real click on a game policy card calls `setPolicySigned(12, true)` and not `enactPolicy` (hook, see part 3). The game's own UI never uses `enactPolicy`.

Verdict: the condition is not found. It is not slot, policy id, available list, silver, influence or level. The function is native code, and no dump of the decompiled body is in this repo. The call path that works for a real player is `Region:setPolicySigned`. Use that. Treat `enactPolicy` as an AI or unused path. Remaining ideas (not tried): development points (a Region or pawn field that raises them), an unlocked tier from the development tree, calling it for another region.

## 3. Real click on a game policy card placed by Lua

Method: command `menu_probe_show` puts a `policyWidget_C` for policy 12 at viewport (300, 300). The OS mouse tool (`runlib/osinput.py`, spec 07) focused the game window (rect 629,285 to 3211,1781), scanned a 30 px grid with `menu_probe_read` (`button_hovered`), and clicked the first hovered point. Hooks were set on `Region:setPolicySigned` and `PawnCPP:enactPolicy`.

Result (run `pf-click`, one launch, no human needed):
- The hover scan found the card at window offset (470, 500) (the card sits at an offset because of the window frame and DPI scale).
- Before the click `policiesSigned` = []. After one click it was [12].
- The hook saw exactly one call: `Region:setPolicySigned(12, true)` on region Nusslohe. No `enactPolicy` call.
- No crash. The cursor was restored. The card was removed with `menu_probe_hide`.

Verdict: a Lua-placed game policy card works with a real click. It signs the policy with `setPolicySigned`. A mod can poll `policiesSigned` (or hook `setPolicySigned`) to react to a click. Not tried: clicking to unsign (the toggle), tooltips, many cards at once.

## 4. Menu choice (b or c): evidence only

This is the user's decision. Evidence:
- Option b works end to end now: the card shows (screenshot), the real click reaches the game handler, and the effect is a hookable `setPolicySigned` call. No pak is needed.
- Option b limits: cards for policy ids that exist in `DT_PolicyTypes` only; layout is the card layout of the game; no new text without a pak.
- Option c (pak widget) was not tested. It gives full layout and new text, but needs a UAssetGUI widget asset (not proven in this repo).
- Recommendation from the evidence: option b for the first mod menu (a working path today). Use option c only if the mod needs its own layout or new policy rows.

## Changes in the repo
- Unsafe command `policy_enact_sweep` (HarnessActions version 39), fake test, probe scenario and report tool.
