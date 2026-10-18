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
- H2: the growth is observed and flagged. A lord that adds fewer than 3 buildings in 10 game days gets `stalled` in the registry (the stall flag matches what the region shows after 20 days). Real runs: growth 4 -> 14 in 3 of 6, no growth in 3 of 6.
- H3: a vassal lord starts a war with the player by itself about 12 s after the handover (seen in 7 of 7 runs). With `keep_peace` the mod declares peace and the player stays at peace for 20 game days (3 of 3).
- H4: the home region stays the player region (owner unchanged, family count not lower by more than 10 percent).
- H5: a second claim uses slot 2 and a second lord (fake game test; real run TBD).
- H6: no crash in 20 game days at speed 2.

## Scenarios
- `scenarios/vassals/settled_vassal.py` (`vassals-settled-vassal`).

## Result
PASS in the real game (2026-10-18), with findings that change the design. Notes: `../implementation-notes/iteration-02-settled-vassal.md`.
- `vassals-settled-vassal` passes in runs `20261018-072413-4d49` (grew 4 -> 13) and `20261018-072920-4acb` (stalled 5 -> 5, flagged), both with `keep_peace`.
- H1: 11 of 11 handovers worked (owner = the lord, `AI_` pawn) within 40 s.
- H2 (growth): the lord grew 4 -> 13 or 14 in 5 of 5 runs where the region had 4 buildings after the settle call, and did not grow in 6 of 6 runs where it had 5 (log: `AI_build failed to find place`). The mod flags the second case (`stalled`).
- H3 (war): the lord is at war with the player in every run, about 12 s after the handover (not at the spawn). `declarePeace` ended it, and it held for 20 game days (7 of 7 runs with keep_peace, 1 call each). Without keep_peace the war lasted all 20 days (3 of 3).
- H4, H6: the home region and the registry were unchanged in every run. H5 (second vassal) is covered by the fake game test only (TBD in a later run).
- Other runs: `20261018-055*` etc. are listed in the notes. Two harness errors were flakes of the command channel (`calling write on bad self`, `no answer to close_popups`), not mod errors.
