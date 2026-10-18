# M07 iteration 02: settled-vassal

Branch: `feat/M07-vassals-02-settled-vassal` (stacked on PR #190, M07.01). Issue: #191.

## Goal
The player claims and settles a region. The mod notices it and hands the region to a friendly AI lord who rules in the player name (M00 decision 20). This is also the spike: does a handed-over AI lord grow reliably, and does it declare war on the player?

## Changes
- Poll (every 3rd poll): scan the regions. A region owned by the player that is not the home region joins the registry (slot, loyalty 50). When it is settled, the mod hands it over.
- Home region: the owned region with the most buildings at the first sight, saved as `vassals_home_region`.
- Handover: spawn a lord with `spawnNewAILord` (name from `vassals.lord_names`, can build), `addPawnRelations`, `startAI(1, true)`, then `lord_receive_region` (clear owner, lord claim and finalize: the proven route of spike S13). The lord name goes to `vassal<N>_lord`.
- War watch: after the handover the poll reads the lord `enemies` and the relation tags with the player. The state shows `war_with_player`. A war is logged once.
- Growth watch: `vassals_state` reports buildings and families of each vassal region.
- Config: `lord_names`, `scan_every`, `handover_attempts`, `lord_supply` is not used.

## Acceptance criteria
- H1: after the player settles a claimed region, the region owner is the vassal lord within 30 s (real time) and the slot has the lord name.
- H2: the lord builds: buildings of the region rise by at least 4 within 20 game days (rerun of spike S13: seen 4 -> 14; one rerun on 2026-10-13 saw none). Record the result in 3 runs.
- H3: the lord is not at war with the player at any poll in 20 game days (user expects no war). Record if it is.
- H4: the home region stays the player region (owner unchanged, family count not lower by more than 10 percent).
- H5: a second claim uses slot 2 and a second lord; no duplicate lord names.
- H6: no crash in 20 game days at speed 2.

## Scenarios
- `scenarios/vassals/settled_vassal.py` (`vassals-settled-vassal`).

## Result
Not started.
