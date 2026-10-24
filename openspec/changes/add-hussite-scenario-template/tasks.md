## 1. Pak
- [ ] 1.1 Extend `harness/tools/modpak.py` and its tests: tables with named rows (`DT_GameSetupPresets`), op `add` from a named row, fields inside a struct and a map.
- [ ] 1.2 Patch file `mod/InvasionMod/data/scenario_settings/patches/` for the row `hussites_are_coming` (clone of `peaceful_citybuilding`, owner settings, title text, existing thumbnail).
- [ ] 1.3 Build with `pakmod.py buildmod InvasionMod`; check the pak holds no AES key.

## 2. Marker
- [ ] 2.1 Find out if the chosen template can be detected at new game start; store `hussite_template` in ModState or write the finding in `notes/`.

## 3. Real game
- [ ] 3.1 Real run with the OS mouse on slot 0: six templates, click the 6th, read `gameSetup`, start the game, the mod start menu opens. Back up and restore `menu.sav`.
- [ ] 3.2 Pictures: the template row with the 6th selected, and its settings list, in `evidence/`.

## 4. Close
- [ ] 4.1 Update the Checked by lines, the wiki and the skill `harness-pak-mod`.
- [ ] 4.2 `CHANGELOG.md` under Unreleased.
- [ ] 4.3 Archive: `openspec archive add-hussite-scenario-template --yes`.
