# M09 iteration 02: notes

## Findings
- The housed path works with the same plot build as the old `refugee-wave` scenario: 5 plots, 16 game days until the homeless count was back at the base.
- The timeout path uses the M04 route (`homeless_rebel`, home mode): the families are removed and a bandit squad appears at their homes. 5 families gave bandit units (squads of 2 families).
- Speed: speed 3 crashed the game in this scenario (access violation in `process_simple_actions`), as it did for M04 notes. Use speed 2.
- A poll of the regions with `core.listOf` (`:get()` unwrap on region actors) every 2 s may be unsafe. The poll of this feature now uses direct indexing. This is a guess: the crash cause is not proved.

## Open
- TBD: the timeout 45 game days; a wave of more than 6 unhoused families turns only 6 in one go (the rest stay until the next poll; the wave ends `rebelled` after the first go, so the rest stay homeless). A later iteration may repeat the check.
- The bandit families are counted in `refugee_bandit_families`, but they are not part of the buy-back pool of M04 (`bandits_outstanding_families`).
