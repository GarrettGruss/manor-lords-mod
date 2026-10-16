# M13: manor-stronghold

Feature folder: `manor_stronghold`. Batch 6.

## Goal
The manor is the stronghold. The player upgrades it through builds and the tech tree: more storage and a larger retinue.

## Player rules (from M00)
- Shared manor upgrades, open to both paths:
  - Manor storage: more capacity. Goods in the manor are the hardest for raiders to reach.
  - Retinue capacity: a larger retinue.
- The manor is the safest store (M03 storage tiers).
- Later layer (deferred): if the town falls but the manor holds, raiders loot and leave when supplies or morale run out.

## Current state
Not started.

## Proven building blocks
- Goods in the Keep count in the region stock: `docs/harness/12-manor-exploration/implementation-notes/storage-m1.md`.
- Capacity is a field of the `buildingStats` row: `docs/harness/13-mod-inspection/implementation-notes/storage-and-manor-unlock.md` (capacity effect not measured).
- Manor levels and module paks: `docs/harness/12-manor-exploration/implementation-notes/manor-lv3.md`, `manor-module-pak.md`, `workaround-m2.md`, `worker-slots.md`.
- Manor limit: `docs/harness/13-mod-inspection/implementation-notes/manor-limit-99.md`.
- Bailey buildings: `docs/harness/17-bailey-buildings/implementation-notes/bailey-buildings.md`.
- Retinue size and garrison limit hook (12 to 36): `docs/harness/13-mod-inspection/implementation-notes/larger-formations.md`.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-manor-tech-units.md`.
- Row ids: `docs/harness/23-row-id-range/README.md`. Proposed block: building ids 2300 to 2399 (rule in `feature-breakdown.md`).

## Tunables (M00)
- Storage capacity per upgrade level.
- Retinue size per upgrade level.

## Dependencies
- M12 (the nodes). M03 (storage tiers).

## Open questions
1. Can the mod change manor storage capacity? Likely (row write plus an instance copy). Not measured.
2. Can the mod change real retinue size? Unknown (M00 open question 16). The garrison hook changed a limit, but not real recruits.
3. Do raiders stop at the manor? No raid was run against the Keep. Needed for the deferred "manor holds" layer.
4. How many upgrade levels are in version 1?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | manor-storage | Manor storage capacity rises by upgrade. | not started |
| 02 | retinue-capacity | Retinue size rises by upgrade. | not started |
