# A/B results of the combat levers (spec 25, plan steps 2 and 3)

Date: 2026-10-16. Game 0.8.111, fixture `base`, no pak. Scenario `combat-levers`, one fight per run, game speed 3. Issue #129.
Statistics: permutation test and Cohen's d (`ab-statistics.md` of spec 10). Alpha 0.1. N is the number of runs per side. Small samples: a heuristic, not proof.
Tool: HarnessActions version 51 (new commands `unit_stats`, `set_unit_stat`, `combat_hook`; `DT_Items` fields `def`, `block`, `att`, `armorPierce` can now be read and written).

## Result table

| Lever | Method | Test | N | Effect | p | Run ids | Risk |
|---|---|---|---|---|---|---|---|
| L1 hook `SMUnit:CombatHit` | `RegisterHook`, observe only | One fight, 19 deaths | 1 | 0 calls. The hook registers but never fires | n/a | `20261016-043827-0ff2` | Dead end. The game calls it natively, not through ProcessEvent. No per-hit lever from Lua |
| L2 live `def` and `block` of spawned units | `set_unit_stat` (Lua write, read back per unit) | 32 militia (`spearMilitia`) against 36 Brigands: normal against def 0 and block 0 | 6 / 6 | Militia loss rate 0.33 to 0.61 (x1.9, d 3.35). Bandit deaths 36 to 1.5. Militia won 6 of 6, then 0 of 6 | 0.002 | suite `20261016-053450-2554` (runs `-001` to `-012`). First suite `20261016-044317-332a` (2 of 12 runs had no contact, replaced by the rerun) | Works and holds for the whole fight. Per unit, live, lost on game restart. Units spawned later need the write again |
| L2b same, def raised above normal | `set_unit_stat` def 32, block 39 on militia | Militia against 50 bandits (32 `militiaFoot` + 18 Brigands) | 6 / 6 | Militia loss rate 0.56 to 0.59 (p 0.045, d 0.8, no gain). Bandit deaths 6.5 to 17 (x2.6, p 0.022) | 0.045 / 0.022 | suite `20261016-050402-ad20` (variant `live-def32-block39`) | Raising def does not make militia survive better. It makes them kill more |
| L2c same, def 62 and block 60 (retinue values) | `set_unit_stat` | same fight | 5 / 5 | Loss rate 0.56 to 0.59 (p 0.36, inconclusive). Bandit deaths 7 to 17 (p 0.16, inconclusive). Militia won 0 of 5 | 0.36 | suite `20261016-055329-3bdb` (variant `live-def62-block60`) | Armor alone does not win the 1.5 times fight |
| L3 `DT_Items` shield 271 `def` 30, `block` 40 | `datatable_write` on `itemStats` before the spawn (restored after) | same fight | 6 / 6 | The item value does change spawned units (mean def 7 to 32, block 8 to 39). Only militia use shield 271. Loss rate 0.56 to 0.73 (p 0.002, d 2.55). Bandit deaths 6.5 to 20 (p 0.006). Militia won 0 of 6 | 0.002 | suite `20261016-050402-ad20` (variant `shield271-def30-block40`) | Works as a Lua write. Gambeson 163 is also worn by bandits (a write there raised their def too). More armor gave more kills and more own deaths in this fight |
| Real heavy unit `retinue_tier3` (def 62, block 60, att 5 weapons, armorPierce 2) | Spawn the template | 36 retinue against the same 50 bandits | 5 / 5 | Militia loss rate 0.56 to 0.22 (d -4.6). Bandit deaths 7 to 50 (all). Won 5 of 5 against 0 of 5 | 0.008 | suite `20261016-055329-3bdb` (variant `retinue-tier3`) | Not a lever on militia. It shows that armor plus weapon together reach the target |

Baseline facts (from `unit_stats`, mean per unit): `spearMilitia` att 4.0, def 7.2, block 7.75. `militiaFoot` att 5.0, def about 5, block 2.9. `Brigands` att 2.4, def 2.9 to 3.2, block 1.3, charge 2.8. Retinue gear (item 293 def 60) is not worn by militia.

## Reading the result

- Unarmored takes more damage: yes, measured. Removing def and block (L2) raised the militia loss rate 1.9 times, and the bandits lost almost nobody. The 2 to 3 times damage target for "unarmored against armored" is reachable by this live write. The loss rate stops at 1.0 and the fight ends when the group routs, so the ratio of deaths is capped. The raw damage ratio is larger than 1.9.
- Armored beats 1.5 times more bandits: not reached by armor alone. Def 32 or 62 on militia did not lower militia deaths. The militia att 4 and no armor pierce cannot kill 50 bandits before the group routs. The full retinue unit (att 5 and armorPierce 2 weapons, def 62, block 60) wins 5 of 5 with 0.22 loss rate. So the M00 target is reachable only when weapon values rise together with armor.
- Not tested: a live write of `att` and `armorPierce` together with def (the missing piece for militia), a pak that changes `DT_UnitTemplates` equipment, and the loss of fights at 2 times the size. A fight ends by "calm" (no death for 10 wall seconds), which is a rout or a stand-off. Time to rout was not measured on its own; `fight_wall_s` is the proxy (def 0: 41 to 24 s, p 0.002).

## Recommendation for the mod

1. Use the live write (`SMUnit` stats through a Lua mod, same code as `set_unit_stat`) for unarmored lethality: lower `def` and `block` of bandit-side or unarmored units after spawn. It is proven, strong and needs no pak. Repeat the write for each new squad (spawn hook or poll).
2. For armored units use item values plus weapon values. Raise `DT_Items` `def`/`block` (Lua write, works for units spawned after it) for items that only the player side wears (shield 271, retinue armor 293), and also raise `att` or `armorPierce` of the weapon, or give militia the retinue equipment ids through a pak on `DT_UnitTemplates` (not tested). Armor alone is not enough.
3. Do not plan on `CombatHit` (L1 is dead).
4. Open for the next spike: live write of `att` and `armorPierce` on militia (one `set_unit_stat` call, no code change), then the pak route if a stable item-level lever is wanted.

## Method notes

- A run is one fight. Runs are interleaved by the suite. A run with fewer than 3 deaths in total fails (two runs of the first suite had no contact and were rerun).
- The player group is the player pawn's squad at the fixture position; bandits spawn 2500 units away. Group sizes come from `maxSize` (32 militia, 32 `militiaFoot`, 18 Brigands, 36 retinue).
- A live write on all living units of a side reads each value back (`changed == alive`).
- The CombatHit hook is a pre-hook only and changes nothing.
