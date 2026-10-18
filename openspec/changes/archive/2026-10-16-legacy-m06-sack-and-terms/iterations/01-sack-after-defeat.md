# M06 iteration 01: sack-after-defeat

Branch: `feat/M06-sack_and_terms-01-sack-after-defeat`. Issue: #173.

## Goal
A lost battle sacks the town. The game continues. The sack uses the native mechanics through `HarnessSack` (M00 decision 8).

## Design
1. New feature `sack_and_terms` (requires `raid_behavior`). Config table `sack_and_terms.sack` in `config.lua`.
2. Lost battle (TBD, rule chosen by the agent). A role raid (lord army) is a lost battle for the player when it starts to leave for the reason `loot` or `time`: the raid took what it wanted, or stayed to the time limit, and the player did not beat it. The reason `losses` (the raiders lost `leave.loss_share`) is a won battle. No sack. A battle that ends with a raid that was paid off (iteration 02, reason `terms`) is not lost.
   - Why this rule: the mod has no captain and no battle result. The raid tracker (M03.02) already has the three reasons. Reading player squads would add many unit reads (crash history, M03).
3. Sack size (decision 15, 28). Share in percent = `share_min` + (`share_max` - `share_min`) x (difficulty - 1) / 2. Defaults 20, 50: difficulty 1 gives 20, 2 gives 35, 3 gives 50. Linear for now. Every count rounds up. The raid size class does not change the sack yet (TBD).
4. The sack takes that share of: standing buildings (method `collapse`, TBD: `fire` is possible), each good of the stock, and families (whole families, `HarnessSack.sack_people`).
5. Keep people alive (spike S8): at least `min_families_left` families stay, except for a fatal sack (point 6).
6. Repeated sacks (M00): a window counter. The first sack starts a window of `window_days` game days. Each sack in the window adds one. The sack that makes the count reach `limit` is fatal. A fatal sack removes all families, and the game ends by its own rule (depopulation). `fatal.enabled = false` only flags it. Defaults: window 360 days, limit 2 (TBD, M00 gives no numbers).
7. Not here: the loss of the great raid's final battle (decision 27, TBD), terms (iteration 02), fallback capital (iteration 03, needs M07).

## Changes
- `raid_behavior`: `watch_leave(fn)` hook, called once when a role raid begins to leave, with the raid summary.
- New `features/sack_and_terms/{init,rules,world}.lua`. Shared module `HarnessSack` is added to `mod.json` `shared`.
- ModState keys: `sack_count`, `sack_window_start`, `sack_window_count`, `sack_last_day`.
- Named commands: `InvasionMod.sack_state`, `InvasionMod.sack_now` (forced sack, optional `difficulty`), `InvasionMod.sack_set_fatal` (session switch).

## Acceptance criteria
- A1: the sack share at difficulty 1, 2, 3 is 20, 35, 50 percent (pure rule, fake tests).
- A2: after `sack_now` at difficulty d, standing buildings fall by ceil(share x standing) (allow +/- 1 for ruins already present), each good of the stock falls by 15 to 55 percent at difficulty 1 to 3 (ceil per good, total range), families fall by ceil(share x families) but at least 1 family stays.
- A3: the population is above 0 after a non-fatal sack. The game does not end. No crash.
- A4: a raid that leaves with reason `loot` or `time` triggers one sack. A raid that leaves with reason `losses` triggers none.
- A5: two sacks in the window reach the limit: `fatal` is true. With `fatal.enabled = false` the village still has people. A sack after the window starts a new window (count 1).
- A6: the counter is kept in ModState.

## Scenarios
- `sack-and-terms-sack` (real game): difficulty 1 and 2 by `--env INVASION_DIFFICULTY`. Forced sack, then census ranges (A2, A3), second sack with fatal switched off (A5).
- `sack-and-terms-raid-sack` (real game): small forced role raid; waits for the leave; checks the sack count after a `loot` or `time` leave (A4).
- Fake game tests: `harness/tests/test_fakegame_sack_and_terms.py`.

## Result
PASS in the real game (2026-10-18, save of day 205: 24 buildings, 10 families).
- `sack-and-terms-sack`: difficulty 1 `20261018-050628-0dab`, 2 `20261018-050747-d64d`, 3 `20261018-051320-061d`.
- `sack-and-terms-raid-sack`: difficulty 1 `20261018-050944-cbde` (leave by loot, one sack), difficulty 2 `20261018-051417-6f67`.
- Fake tests: 11 in `test_fakegame_sack_and_terms.py`. Full suite: only the 5 known install_scripts failures.
- Not verified: the fatal sack in the real game (depopulation end), fire method, the `time` reason in a real run.
- Deviation: goods are taken by the mod (`world.take_goods`), not by `HarnessSack.sack_goods`. See the notes.
