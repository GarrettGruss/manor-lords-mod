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
