# Feasibility: manor, tech tree, laws, units (M00)

Date: 2026-10-15. Reviewer: read-only pass over the evidence in `docs/harness/`, `mod/shared/` and `mod/PolicyMenu/`. No game was run. No Python was run.
Scope: manor storage and retinue, tech tree and laws, Hussite units, army counters, veterancy, armour damage, war economy. Open questions 10, 12, 13, 16. Unit balance targets.

## Rating key
- PROVEN: shown in the real game by a note.
- LIKELY: the calls or data exist. Not yet combined in one test.
- UNKNOWN: no evidence. Needs a spike.
- BLOCKED: notes show it is not possible from Lua or pak.

## Mechanic table

| Mechanic | Rating | Evidence | Approach | Main risk |
| --- | --- | --- | --- | --- |
| Manor store (goods put in, kept, taken out) | PROVEN | `openspec/changes/archive/2026-10-15-legacy-12-manor-exploration/implementation-notes/storage-m1.md`: scenario `manor-storage`, 3 of 3 real runs. Mod-defined store on the Keep (type 57), capacity 200. | Lua (`mod/shared/HarnessManor`) | The base game does not fill the Keep store. Workers do not carry to it. The store rule is ours, not the game's. |
| Manor storage capacity (game limit) | LIKELY | `worker-slots.md`: `storageLimitGeneric` on row 57 of `buildingStats` writes and reads in Lua. The instance copies it at creation, so a write to the instance is also needed. `storage-and-manor-unlock.md` (community Lua mod) changes the same fields, not tested here. | Lua (row write plus instance write), pak as fallback | Effect of a higher cap on real stock is not shown. Existing Keeps keep the old instance value unless it is written. |
| Retinue capacity (manor garrison limit) | UNKNOWN | Value hook PROVEN: `manor-lv3.md` round 10, `HarnessGarrison` changes `getModularGarrisonLimit` 12 to 36 (run s90h-1). Native retinue limits 12 and 24 are code constants (`13-mod-inspection/implementation-notes/larger-formations.md`). | Lua post-hook (`mod/shared/HarnessGarrison`), opt-in by env | The hook only runs for script calls. Native callers keep 12 or 24. Effect on real recruiting is not tested. |
| Manor upgrade by build (Lv3 tower) | LIKELY | `manor-lv3.md` round 10: Lv3 tower built mouse-free with pak B (`IsConstructed` true on day 11). Rows 81, 83 and 98 hold the manor levels. | Pak (row 57 and mesh rows) plus Lua build flow | This is a harness build flow. The player's tech-tree upgrade path is not tested. |
| Tech tree with two exclusive paths | UNKNOWN | `DT_RegionDevelopmentTech` exists (`10-invasion-testability/implementation-notes/game-data-tables.md`), not read. `requiredTech` field exists on `buildingStats` (`manor-lv3.md`). Development panel and `getNumDevPointsSpent` exist (`16-policy-edicts/implementation-notes/policies.md`). | Lua read of the table, then pak for node rows (to test) | Node effects may be C++ only. Path lock and its removal are not known. |
| Laws: game effect (conscription, forced labor, scorched earth, militia rights, trade pacts) | BLOCKED | `policies.md`: 18 policy rows, effects are in C++, "a pak can add rows ... but the effect is C++". `policy-followups.md`: `enactPolicy` returns false. Signing policy 12 shows no effect on food or approval. | None for the game effect | A new law cannot run the game's own effect from Lua or pak. |
| Laws: mod-owned effect | UNKNOWN | Signing works: `Region:setPolicySigned` PROVEN (`policy-followups.md` part 3, real click). Setters `changeTaxRate`, `changeInfluence` exist in the jmap, not tested. | Lua state plus existing setters | Each law needs its own logic. The setters are not proven to change the game. |
| Conscription (families become militia) | UNKNOWN | Militia spawn PROVEN: `spawn_units` with `spearMilitia` and others (`spike-S7.md`, `spike-C1.md`). No evidence that families can be turned into militia. | Lua (spawn) plus Lua state for families | No way to move a family into a militia squad is shown. |
| Forced labor on walls | UNKNOWN | `Region:assignFamily` PROVEN for storehouse, granary and Keep workplaces (`worker-slots.md`). Walls as a workplace not tested. | Lua (`assignFamily`) | Walls are not a worker slot in the notes. |
| Scorched earth (burn own buildings) | UNKNOWN | `spike-S6.md`: `SetFireToNumBuildings` had no visible effect. `CollapseNumBuildings` not tried (`free-walls.md`). | Lua or game call (not chosen) | No working call found yet. |
| War economy (workers to fletchers, smiths, walls) | LIKELY | `assignFamily` PROVEN on storage workplaces (`worker-slots.md`). Crafting workplaces not tested. Food and trade loss not measured. | Lua (`assignFamily`) | Unknown if smith and fletcher workplaces accept families the same way. |
| Hussite units from existing foot units | LIKELY | Spawn by template PROVEN (`spike-S7.md`). Mapping: sword men = `militiaFoot`, spearmen = `spearMilitia`, pikes = `militiaPole`, crossbowmen = `crossbowMilitia` or `mercenary_crossbowmen`. Side comes from the owner pawn (`player` or `bandit`, `spike-S7.md`). | Lua spawn (`HarnessBattle`), pak for names and text | No separate Hussite side in the data. The bandit side is the only other side. Handgunners: no firearm template found (UNKNOWN). |
| Army counters (pike against sword, heavy against sword) | LIKELY | `spike-C1.md`: suite `counters-ab`, 8 runs. Spear against sword loss rate 0.72, heavy against sword 0.15 (`different`, p 0.029). | Lua A/B (`counters-ab`) | Shields and pavises: no shield template, `shields` is an item id array (not tested). Horse counters: no horse template in the base game. |
| Archers against light raiders | UNKNOWN | Bow templates spawn (`spike-C1.md`). Bow against brigands not measured. Bow stats do not show at spawn. | Lua A/B (same method as counters) | No measured result yet. |
| Veterancy (units keep experience) | PROVEN | `spike-C2.md`: scenario `veterancy`, 3 of 3. Mean `combatExperience` 0.54 to 1.15, 0.39 to 0.94, 0.61 to 1.31 over two fights. Kept for a game day. Writable with `set_squad_experience`. | Lua | Fresh units start at 0. The template value is not used. |
| Unit stat numbers (cost, maxSize, minHouseLv) | PROVEN | `spike-S7.md`, scenario `unit-data`: `maxSize` 32 to 10 changed the next squad to 10 units. Criterion C3 verified. | Lua (`HarnessDataTable`) | Strings, arrays and new rows not tried. Stats like `att` and `def` are not in the table. |
| Much higher damage to unarmored units (2 to 3 times) | UNKNOWN | `DT_UnitTemplates` has no damage or hit point field (`spike-S7.md`). Armour is an item id array (`armours`), not tested. `DT_Items` read only `Value` and `Weight` (`datatable-check.md`). No damage multiplier found in any note. | Not chosen. Needs a spike | The effect may be in C++ only. That would block this pillar. |
| Armour investment pays off (armoured militia beats larger bandit group) | UNKNOWN | Depends on the row above. Counter method exists (`counters-ab`). Armour change not tested. | Lua A/B plus item change (to test) | Same as the row above. |
| Second invader (free company, Q12) | LIKELY (partly) | Mercenary hire PROVEN (`spike-P5.md`, 3 of 3). `DT_MercenaryCompanies` has 11 rows. Hostile use of a company is not shown. | Lua (spawn on bandit side, or a new side) | Mercenaries are hired for the player. A hostile company side is not in the notes. |

## Open questions

- Q10 (path choice undone?): UNKNOWN. A mod flag can be reset in Lua (LIKELY). Whether the game lifts a node lock is not shown.
- Q12 (second invader needed?): Feasibility is LIKELY only for a bandit-side or mercenary-side group. It is not shown that a second hostile faction works as an AI side. This is a design choice more than a test.
- Q13 (which foot units stand in for sword men and handgunners?): Answered for sword men, spearmen, pikes and crossbowmen (see the table). Handgunners: no template found (UNKNOWN). Use crossbowmen as the stand-in until a firearm row is found.
- Q16 (can the mod change manor storage, retinue size and the armour factor?):
  - Manor storage: Yes, by Lua row write (LIKELY). The mod store is PROVEN.
  - Retinue size: The hook changes the value (PROVEN). The effect on recruits is UNKNOWN.
  - Armour factor: UNKNOWN. No field found.

## Unit balance targets

| Target (design doc) | Rating | Note |
| --- | --- | --- |
| Unarmoured unit takes 2 to 3 times the damage | UNKNOWN | See the armour row. |
| Armoured militia beats a bandit group 1.5 to 2 times its size | UNKNOWN | Measurable with `counters-ab` once the armour effect exists. |

## Top 3 risks

1. **Armour and damage are not found (UNKNOWN).** This blocks the "armour matters" pillar. If the damage rule is in C++ only, this pillar is BLOCKED and the design must change.
2. **The retinue cap is native.** The Lua hook changes the value Lua sees. The native recruit path may still use 12 or 24. A recruit test with the hook on is needed before the design relies on it.
3. **Laws and tech effects are C++.** Pak and Lua cannot add the game effect of a law. Each law needs mod-owned logic. The tech tree node effects are not read. The scope of the tech tree and laws may be much larger than the design assumes.

## Spikes needed

1. **Armour and damage (blocks pillar 4).** Search the jmap for damage, armour and hit fields on `Unit`, `Squad`, `Stat`, `UnitTemplate` and `Item`. If a field exists, write it and run `counters-ab` as an A/B. Also test a write to the `armours` array.
2. **Retinue cap.** With `HARNESS_GARRISON_BONUS` set, recruit above 12 by a real click or by the retinue editor path. Count retinue members before and after.
3. **Tech tree data.** Read `DT_RegionDevelopmentTech` rows (names and plain fields only, no soft fields). Check `requiredTech` on a row. Write one node and see if a game gate opens.
4. **Mod-owned law.** Pick one law (for example forced labor). Build its state in Lua and its effect with an existing setter. Measure one metric with an A/B.
5. **Smith workplace.** Assign a family to a smithy with `assignFamily` and check that it works. This is needed for the war economy row.

Also open: a firearm template search (Q13). Horse rows would need a mod pak, since the base game has none.
