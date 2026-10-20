# Tags limits (task 1.1)

Test scenario `harness/scenarios/spike_tags_limits.py` (hidden), mod commands `InvasionMod.spike_tags_write` and `spike_tags_read` (feature `mod_state`, Lua `FName` appends). Backup first: `SaveGames-backup-283-205317` (314 files). Saves only through `save_game`.

Runs: write `spike-tags-w2` (slot saveGame_52) and `spike-tags-w3` (slot saveGame_54); read (load) `spike-tags-r1` (from 52) and `spike-tags-r2` (from 54). `spike-tags-w1` was a harness_error (argument name clash, no game change).

| Entry set on the player pawn | Written | After save and load |
|---|---|---|
| 10 entries, 43 chars each | yes | 10 back, same text |
| 100 entries, 43 chars | yes | 100 back |
| 1000 entries, 43 chars (43,000 chars) | yes | 1000 back, same text |
| 1 entry of 4000 chars | the engine turns the name into `ERROR_NAME_SIZE_EXCEEDED` (24 chars) at write time | the same error name comes back; the content is lost |

- Pawn Tags total after the writes: 1131 (30 before). Write time: under 5 ms for 1000 entries. Read of 1131 tags: 2 to 5 ms.
- Save time (`save_game`, to a settled slot): 6.7 s and 7.1 s. Boot with a save to READY: 34 to 35 s (31 to 32 s boot phase), the same range as a normal boot (about 34 s). No slowdown seen.
- Save file size: 2,632,685 bytes (saveGame_49, older) against 2,635,442 (saveGame_54, with 1131 extra Tags): about +3 KB.
- No crash, no failure of save or load.
- Limit found: one Tag name must be under 1024 chars (confirms `MAX_NAME_CHARS = 1023` of ModState). A longer text is not truncated: it is destroyed. The count limit was not reached at 1000 (not tested above that).
- The two "lng" checks in the runs failed on purpose: that is the finding.
