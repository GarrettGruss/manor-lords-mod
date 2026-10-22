## 1. Spike (game agent; notes in `notes/`)

- [ ] 1.1 Find the new game and custom game settings of the game: widget classes, the settings object, and fields about raiders, bandits or their frequency or difficulty. Check if Lua can read them in a loaded game. Write `notes/game-settings.md`.
- [ ] 1.2 Check if the mod can add an option widget to the new game menu and get its value into the new game. Reuse the widget cloning of `core/menu.lua` (branch `feat/add-mod-menu-access-rule`, issue #308). Write `notes/new-game-menu.md`.
- [ ] 1.3 Check that the value survives save and load through the mod state (`openspec/specs/mod/mod_state/spec.md`). Save only with the guarded `save_game` action. Write `notes/save-load.md`.
- [ ] 1.4 Make a named command that sets the difficulty at any time (no "once" limit). Check its limits against `invasion_pick_difficulty` and its test scenario `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`. Write `notes/set-command.md`.

## 2. Decisions (owner)

- [ ] 2.1 Confirm the assumptions in the proposal.
- [ ] 2.2 Pick the source of the value: the game setting (A) or a mod option (B), based on the spike.
- [ ] 2.3 Decide the final name of the setting and of the command.
- [ ] 2.4 Decide what happens in an old save with no stored value (use the default `invasion.difficulty`?).

## 3. Implementation (gated on the spike result and section 2)

- [ ] 3.1 Add the setting to the new game menu, or read the game setting.
- [ ] 3.2 Store the value in the mod state and read it back on load.
- [ ] 3.3 Remove the three difficulty buttons and the pick prompt banner from the raid menu and the invasion feature.
- [ ] 3.4 Change the set command so it works at any time and re-plans an unspawned raid.
- [ ] 3.5 Update the test scenarios and fake game tests; update the "Checked by" lines of the delta specs.
- [ ] 3.6 Update `CHANGELOG.md`, the mod changelog, the wiki and the affected skills.
