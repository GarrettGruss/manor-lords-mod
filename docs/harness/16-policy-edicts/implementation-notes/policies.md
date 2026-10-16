# Policies: model, live values, enact test

Date: 2026-10-12. Fixture `base`, one game (run `s16-b`), no crash. Game version 0.8.111.

## Where policies are defined
- DataTable `ManorLords/Content/NotStronghold/Data/DT_PolicyTypes` (struct `Policy`: ID, tier, Name, descr, timeLeft, Icon).
  The row name is the policy id (0 to 18). The fields `ID`, `tier` and `timeLeft` are 0 in every row. Texts are in `DT_Translation_Policies` (keys `policyID_<n>`, `policyID_<n>_descr`).
- Code: enum `EPolicyType` (Unknown 0, HuntingGround 2, NightWatch 4, BathhousePleasure 7, WeeklyMass 8, CleanWater 10, StrictFasting 12, Coinage 15,
  GuildBrotherhood 16, PublicWeaponBan 17, PurchasePrivilage 18) and `PolicySettings.BasePolicyTypes`.
- The effects are in C++. The rows hold no effect data. Several rows say "[not implemented]" or "WIP".

## Policy list (row: name, text)
1 Hardship (peasants eat half as often, loyalty falls 1% a day); 2 Hunting grounds; 3 Craftsmanship; 4 Night watch ([not implemented]);
6 light_punishment (WIP); 7 Bathhouse pleasures ([not implemented]); 8 Weekly mass ([not implemented]); 9 Smallholdings; 10 Clean water;
11 Small land tax (1 silver per family per month from regional wealth); **12 Strict fasting: "Citizens skip every 5th meal. Reduces food consumption, decreases approval."**;
13 Forest preservation; 14 Tithe (10% of surplus food becomes influence); 15 Coinage (+10% taxes, -10% wealth); 16 Guild Brotherhoods;
17 Public Weapons Ban (+25% proficiency, -10 approval); 18 Purchase Privilage. Rows 0 and 5 are placeholders.
There is no timed policy: `timeLeft` is 0 everywhere and the sign state has no expiry.

## Classes, structs, functions (jmap)
- `Policy`, `HistoricalPolicy` (12 bytes, no fields), `PolicySettings.BasePolicyTypes`, `EPolicyType`.
- `PawnCPP`: `enactPolicy(Region, slotNo, policyID) -> bool`, `availablePolicies` (int array), `silver`, `influence`.
- `Region`: `policies` (Policy array), `policiesSigned` (int array), `getAllAvailablePolicies`, `getMaxPolicies`, `hasPolicy(ID)`, `setPolicySigned(id, bool)`,
  `getNumDevPointsSpent`, `Approval`, `summedApprovalFactors`, `publicOrderMemory`, `summedPublicOrderFactors` (ApprovalMemory arrays), `getSummedFactorsRecentPast`,
  `getPredictedApprovalLossFromTaxes`, `changeTaxRate`, `GetFamilyConsumptionData(familyID)`, `supplies_food`, `regionalWealth`.
- `ApprovalMemory` (Type EApprovalFactorType, day, expirationDay, count, past, effectByPopulation): a timed approval effect.
  `ApprovalEffect` (RowName, Value), `Approval` (table row: HigherApprovalRate, ImpressionRowName, Effects, Color), `ApprovalComponent` (`ApprovalDataTable`, `GetApprovalData`),
  `ApprovalSettings`, `RTSMultiEngineCPP:GetDefaultApprovalRateForFactor`.
- `EApprovalFactorType` (34 values): hunger, starvation, cold, ... `hardship` (21), `taxation` (24), `SatisfiedAmenities` (33).
- `FamilyConsumptionData` (ItemCategory, ItemSubcategory, ItemType, Period, DaysLeft, DaysInCurrentCycle, AffectedByPerks). `Punishment` (devPoints, loyalty, growth, development, Items, policyLock, techLock, forTime, ...).
- UI: `developmentPanelTree_C` (the development panel; `updatePolicies`, 20 `policyWidget_N` children, `allPolicyWidgets`), `policyWidget_C` (policyID, policyTier, Region, wip, Button_22),
  `BigTooltipPolicy_C`, `WBP_Approval_C`, `FamilyConsumptionTooltip_C`. `PawnCPP:toggleDevelopmentPanel`.

## Live values (fixture base, region Nusslohe, level 1, 35 people, approval 71)
- `getMaxPolicies` 1. `Region.policies` empty. `policiesSigned` empty. `getAllAvailablePolicies` = [2, 4, 7, 8, 10, 12]. `PawnCPP.availablePolicies` empty.
- Silver 83, influence 660, regional wealth 91, dev points spent 0, taxes approval loss 0.
- Approval factors (ApprovalMemory, 5-day blocks): SatisfiedAmenities +6, SatisfiedMarketCommodities +4, foodVarietyGood +4 (past blocks +3, +2, +2).
- Panel widgets (live): ids 12 and 2 are tier 1 and not WIP; ids 7, 8, 10, 4 are tier 2 and WIP; 14, 11, 15, 16, 17, 18 are tier 1 widgets; id 6 is WIP.

## Enact test
- `PawnCPP:enactPolicy(region, 0, id)` returned **false** for ids 12, 2, 10 and 4 (slot 0 is the only slot). Nothing changed (policies, signed, approval, silver, influence). The cause was not found.
  Clue: `PawnCPP.availablePolicies` is empty. The UI Blueprints never use `enactPolicy` (no `CallFunc_enactPolicy` variable in any UI function), so it is probably a code or AI path.
  Writing `availablePolicies` was not tried (a property write, outside the limits).
- `Region:setPolicySigned(12, true)` works: `policiesSigned` becomes [12]. `setPolicySigned(12, false)` empties it. This is the remove call.
- The game's own click path gives the same result: toggling the panel (`toggleDevelopmentPanel`) and calling the release handler of the live `policyWidget_2` (policy 12) set `policiesSigned` to [12].
  A hook on `enactPolicy` saw no call. So the UI does not use `enactPolicy`.
- Effect over game days at 8x (4.2 days unsigned, 4.1 days signed by command, 5.1 days signed by the widget): approval stayed 71, no new approval factor (no `hardship`), silver, wealth and `supplies_food` did not change.
  `hasPolicy(12)` stayed false while 12 was in `policiesSigned`. So the signed list alone gave no visible effect in this village.
  Not shown: whether food use fell (no per-family food measure was read; `GetFamilyConsumptionData` returns structs by value and was not called).
- The development panel stops the game clock while it is open.

## Rationing
- Closest policy: 12 "Strict fasting" (skip every 5th meal, less food use, less approval). Also 1 "Hardship" (eat half as often, loyalty -1% a day), but no panel widget has id 1.
- Today the mod can sign or unsign policy 12 (`policy_sign`) and read approval and its factors. Unproven: that signing changes food use.
  Food per family cannot be set from Lua: `FamilyConsumptionData` has only a cycle and days left, no rate field.
- Temporary approval effect: `summedApprovalFactors` is an array of `ApprovalMemory` with `expirationDay`. No add function was found in the jmap. Writing array elements was not tried.
- A new timed ration edict with a real effect needs code. A pak can add rows to `DT_PolicyTypes` and text, but the effect is C++. A pak can change `DT_Approval` effect values.
  The realistic path: a mod-owned edict, with a Lua timer that signs policy 12 and unsigns it later, and its cost applied through game calls (`changeTaxRate`, `changeInfluence`) or a pak.

## Commands added (HarnessActions version 19)
`policy_state` (read), `policy_enact` (game call; refuses unavailable ids or a bad slot; returned false in the real game), `policy_sign` (setPolicySigned), and the spike commands `menu_probe_show`, `menu_probe_read`, `menu_probe_hide`.
Python: `Actions.policy_state`, `policy_enact`, `policy_sign`. Fake tests: `harness/tests/test_fakegame_harnesspolicies.py` (11 tests).
