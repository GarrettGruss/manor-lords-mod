# Squad loan (task 1.6)

Source: `openspec/changes/archive/2026-11-04-spike-loan-units/notes/loan-units-findings.md`.

- Squad loan works: `PawnCPP:addRemoveSquadRequest({Value = id})` removes the squad (no bodies, no crash); `spawnArmy` of the same template after N days returns an equal squad. `loan_enabled` is true.
- Peasant loan is not possible. The owner dropped it (2026-11-05).
- The template of a real squad is not readable from the units. The loan reads it from the `HarnessBattle` registry, or from the table `liege_contracts.loan_templates` by the number of men (32: `spearMilitia`, 36: `retinue_tier1`). Any other size is refused.
- Not verified: a real rallied retinue or militia squad (the spike used spawned squads); save and load of the loan record (fake game only).
