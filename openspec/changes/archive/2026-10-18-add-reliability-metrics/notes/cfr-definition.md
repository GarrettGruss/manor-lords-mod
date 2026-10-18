# The change failure rate needs blame, not only a time window

Found 2026-10-18 in the first git report.

- The git history of this repository covers 9 days (2026-10-09 to 2026-10-18). The window `cfr.window_days` is 14.
- With the planned rule (a feat fails when any fix in the same domain follows within the window), almost every feat in a busy domain failed: `harness/run-launcher` 1.00 (n=83), `unmapped` 1.00 (n=42), `mod/core` 0.98 (n=44).
- So the rule said nothing about the feat itself.

Decision: a feat fails in a domain when a later fix in that domain changes lines that this feat wrote (blame), and the fix comes within `cfr.window_days`. The window stays as a limit. With this rule `harness/run-launcher` is 0.20 and `mod/core` 0.09.

Design decision 5 and the skill spec (requirement 5) are updated.
