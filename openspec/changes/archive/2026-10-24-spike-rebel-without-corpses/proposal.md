# Proposal: spike-rebel-without-corpses

Issue: #484

## Why
`homeless_rebel` removes families with `SMUnit:just_die`. Each dead person is a body. The owner wants the families to leave without bodies, then bandits to appear at the homes.

## What Changes
Spike only. No code, no delta spec. Notes in `notes/`, one lasting fact page in `docs/wiki/concepts/engine-limits.md`, new crash causes in `DANGEROUS_ACTIONS.md`.

## Questions and short answers
- Q1: bodies after `homeless_rebel`? Yes. Each family member becomes a body in `Region.corpses` where it died (0 to 24 000 units from the home). See `notes/q1-bodies.md`.
- Q2: removal without a body? No clean way. `K2_DestroyActor` on any unit crashes the game. `Region:removeWorkerFamilyAt` only deletes the family record. No safe squad or side setter. Best: `just_die` plus `SetActorHiddenInGame`. See `notes/q2-removal-attempts.md`.
- Q3: full sequence with the hide route works (families -2, 6 hidden bodies, 2 squads at the homes). In `playtest-noai` the squads did not raid. See `notes/q3-sequence.md`.
