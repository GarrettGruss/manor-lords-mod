# Spec 28: Live unit tuning

Status: done, awaiting user review (2026-10-16). Real-game check passed (`implementation-notes/real-game-check.md`). Issue: #138. Branch: `feat/28-unit-tuning` (based on `feat/25-combat-lethality`).

## Goal
Let a human and an agent tune the "feel" of combat damage in the running game. The human watches a fight. The tool changes unit stats (att, def, block, armorPierce, morale, charge) for a whole side at once. The change applies at once and also to units that spawn later.

## Non-goals
- No permanent change. Overrides live in the running game only. A restart clears them.
- No pak or data table change (see spec 09 and spec 25 for that).
- No raw eval. Only named commands.
- No balance decision. The tool only finds values; the user decides.

## Facts that shape the design
- `set_unit_stat` (spec 25) changes only units of squads that a harness spawn registered. In a normal game the player levies, bandits and AI lords are not registered.
- Live `SMUnit` writes hold for a whole fight. They are lost for units spawned later and on restart.
- A unit has no owner field. The side comes from the squad id and `PawnCPP.commandedSquads` (spike: `implementation-notes/unit-owner.md`).

## Plan
1. Side detection: map squad id to owner pawn (`isMainPlayer`, `isBandit`, `isAI`). Spike it in the game.
2. Commands in `HarnessBattle`, exposed by `HarnessActions`:
   - `tune_state`: per side and per squad, alive count and mean of each stat, plus active overrides.
   - `tune_set`: write a stat on all living units of a side (or one squad) and store an override.
   - `tune_reset`: remove overrides (all, or one side or field) and restore the first recorded original value of each unit.
   - A 2 s timer re-applies overrides to units that appeared later.
3. Streamlit page `harness/tools/tune_ui.py` with a small client module. Sliders, apply, reset, refresh, spawn test fight, export to `presets/`.
4. Fake-game tests, then a real-game check (`implementation-notes/real-game-check.md`).

## Open questions
- Answered (real-game check): the timer re-applies within 2 s to units spawned later. A unit may fight up to 2 s with the original value.
- Answered (`unit-owner.md`): no `other` squad was seen in a normal game; the side is reported if a pawn has none of the flags.

## Acceptance criteria
- A1: `tune_state` lists player, bandit, ai_lord units of a normal game without registry.
- A2: `tune_set` changes all living units of a side, read back by `tune_state`.
- A3: Units spawned after `tune_set` get the override within the timer period.
- A4: `tune_reset` restores the original values.
- A5: The UI starts with `uv run streamlit run harness/tools/tune_ui.py -- --run <id>` and shows command errors.
- A6: The full unit test suite passes. The real-game check has run ids.

## Restart a tuning session
Run these from the repo root (or the worktree that has the tune code). Only one agent or person may use the game at a time.
1. Start a game that stays open: `uv run python harness\run.py --scenario noop --keep-open --run-id tune-<date>`.
   Wait until the run line says `pass`. The game is then paused at READY.
2. Start the page: `uv run streamlit run harness/tools/tune_ui.py --server.headless true --server.address localhost --server.port 8501 -- --run tune-<date>`.
   Without `--run`, the page uses the newest run that has a commands folder or a `ready.marker`.
3. Open http://localhost:8501. Click Refresh. Unpause the game window to watch a fight.
4. Use "Spawn test fight", change stats per side, click Apply. Overrides are re-applied every 2 s to new units. Reset restores the originals.
5. Export the values you like. Presets go to `openspec/changes/archive/2026-10-16-legacy-28-unit-tuning/presets/`.
6. At the end: stop the Streamlit process (Ctrl+C), then stop the game (`manor-harness` `stop_game`, or close the window). Overrides live only in the running game; they are lost on restart.

Known issue (fixed in e6492dc): a fresh run has no `commands` folder until the first command. The page now accepts a run with `ready.marker`.
First session: run `s28-session-1` (2026-10-16). The user checked the page and approved the tool. No preset was exported yet.
