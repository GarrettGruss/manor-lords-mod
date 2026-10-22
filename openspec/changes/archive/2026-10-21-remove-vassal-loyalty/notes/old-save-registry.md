# Old save registry (task 1.1)

Question: what happens when a save holds `vassalN_loyalty`, `vassalN_submitted`, `vassals_submissions` and `vassals_last_season` in the pawn Tags?

Answer: nothing bad. `ModState` (`mod/shared/ModState/ModState.lua`) keeps an entry with the mod prefix and no registered key as it is and lists it in `dump().unknown`. The feature code no longer registers or reads these keys, so it ignores them. A vassal that was submitted loads as a normal vassal (region and lord are read, nothing else).

Check: fake-game test `OldSaveTests` in `harness/tests/test_fakegame_vassals.py` loads a pawn with those tags. The state command shows the vassal without `loyalty` and `submitted`.

Not checked in the real game. The stale tags stay in the save; they use a few bytes of Tag space (limits: see `spike-mod-state-limits`).
