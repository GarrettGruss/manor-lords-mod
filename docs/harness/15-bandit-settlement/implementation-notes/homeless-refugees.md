# Homeless refugees (part 7, 2026-10-12)

Game 0.8.111. Goal: families that stay homeless and draw down approval, made from Lua without the mouse.
Commands: `family_state`, `family_eject`, `family_add` (HarnessActions version 33, module HarnessHousing). Probe scenario: `probe-refugees` (hidden, mode set by `HARNESS_PROBE`).
No save function was called. Eval was not used.

## Short answer
- Lead 1 works. `Region:SetFamilyHome(familyID, nil, suppress)` makes a housed family homeless at once. The family keeps its members and stays in the family count.
- The game does NOT move the families back on its own, with `suppress` true or false (5 game days watched, both).
- `Region:accomodateHomelessFamilies(nil)` moves all of them back into homes at once.
- Approval falls while families are homeless: 71 to 59 in 5 game days with 3 homeless families (baseline without homeless: flat 71).
- Lead 2 is partly open. `removeFromFamilyIfHasOne(false)` plus `AddNewFamily({unit})` creates a homeless family (families +1, homeless +1), but the game crashed 2 game days later.
- Moving a family into the tent was not tested (no fixture has both a housed family and a tent).

## Lead 1: eject (fixture `base`, region Riesenbuckel, 10 families, all housed)
Call: `family_eject count=3 suppress=...`. The ids are read from `occupantFamilyIDs` of the residential buildings. The ejected ids were 1, 0, 4.
| Run | suppress | Step | Families | Homeless | Residents | Vacant (constructed) | Housed ids |
|---|---|---|---|---|---|---|---|
| s15-f1 | true | before | 10 | 0 | 35 | 2 | 10 |
| s15-f1 | true | after | 10 | 3 | 35 | 2 | 7 (the three are gone from `occupantFamilyIDs`) |
| s15-f4 | false | after | 10 | 3 | 35 | 2 | 7 |
| s15-f2 | false, then `accommodate_homeless` | after accommodate | 10 | 0 | 35 | 2 | 10 |
- Vacant slots did NOT rise (2 before and after). `getAvailableLivingSpace` does not count the freed homes while the families are only homeless. Do not use the vacant slots as a check for this.
- After the eject the homeless count stayed 3 for 5 game days in runs s15-f1 (suppress true) and s15-f4 (suppress false). Housed ids stayed 7. So `SuppressResortResidential` made no visible difference in this window. The game has no timer that rehouses homeless families on its own, at least not within 5 days with 2 free slots.
- `accommodate_homeless` (run s15-f2) rehoused the 3 ejected families at once, in the order of the ids.

## Approval per game day (run s15-f1, same numbers in s15-f4)
Game day 0 is the eject. Baseline (2 days before the eject): 71, 71.
| Day after eject | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Approval, 3 homeless of 10 families | 71 | 69 | 67 | 63 | 62 | 59 |
| Approval, no homeless (run s15-f2, rehoused) | 71 | 71 | 71 | 71 | 71 | 71 |
Run s15-f1 and s15-f4 gave the same values on every day. The fall is about 2 points a day, then faster.
Fixture `manor-bailey` (run s15-f5): 5 homeless families in one tent, 15 residents: approval 15, 13, 12, 12, 10 on days 0 to 4 (the tent does not count as a home).
Read: `Region.Approval` (the same value that HarnessTelemetry reports). `family_state` and `housing_state` now show `approval` and `public_order`.

## Tent as the new home
Not tested. Fixture `manor-bailey` has the tent with 5 families but no housed family (`family_eject home=tent` refused: "only 0 housed families"). Fixture `base` has no tent.
Fact from run s15-f5: the tent is not a residential building (`isResidentialBuilding` false), its `occupantFamilyIDs` lists 5 families, and the game still counts them as homeless.
Open: eject a family on a fixture that has both a house and a tent, with `home=tent` (the command exists).

## Lead 2: new families (run s15-f3, fixture `base`)
Method: take the last living member of a family that has 2 or more living members, call `member:removeFromFamilyIfHasOne(false)`, then `Region:AddNewFamily({member})` (a Lua table with one SMUnit). Done twice in one command.
| Step | Families | Homeless | Residents | Approval |
|---|---|---|---|---|
| before | 10 | 0 | 35 | 71 |
| after `family_add count=2` | 12 | 2 | 35 | 71 |
| game day 1 | 12 | 2 | 36 | 66 |
| game day 2 | 12 | 2 | 37 | 64 |
- The new family ids were 10 and 11. Both members had role 3 (a child).
- The table of one UObject was accepted. `family_state` still showed 10 housed ids, so the new families have no home.
- Residents rose 35 to 37 on days 1 and 2 (the new families pull in residents or the children count again; cause not isolated).
- CRASH: the game ended 78 s after start, about 2 game days after the call (before day 3 was read). `EXCEPTION_ACCESS_VIOLATION reading address 0x3c1` (null pointer). Report: `runs/s15-f3/crash/UECC-Windows-2184228F4CD31C7ACD2ABC9EDEF8135B_0000/`. Logs: `runs/s15-f3/mod.log`, `scenario.log`, `UE4SS.log`, `probe.jsonl`.
- Cause not isolated. Suspects: a child taken out of a family without its own adult (the new family has no adult, so a job or home routine reads a null); or `removeFromFamilyIfHasOne` leaving a stale pointer in the old family. This is an unsafe method until a run shows otherwise.
- Next try (needs a launch): pick an adult member (role 0 or 1) and keep the old family intact; or use `getAllFamilyMembers`; or give the new family two members (an adult and a child).

## Verdict for the user design
Use `family_eject suppress=true` (lead 1). It is stable (3 of 3 clean runs: s15-f1, f2, f4), mouse-free, keeps the families as villagers, and approval falls. `family_add` is not safe yet.
Mod rule for refugees: eject N housed families, do not call `accommodate_homeless`, and do not build homes. The game will not rehouse them in 5 days, but new homes built later may take them (not tested).

## Not verified
- Whether new houses (or the settle letter) take the ejected families later.
- Whether approval keeps falling after day 5, and what happens at a low value (bandits, unrest).
- The tent as `newHome`.
- Whether the `suppress` flag has any effect (no difference seen).
