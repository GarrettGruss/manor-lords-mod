## 1. Menu structure
- [ ] 1.1 Back up `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` and `menu.sav`. Read `DANGEROUS_ACTIONS.md`.
- [ ] 1.2 Find the widget classes, the template list and the settings rows by bridge reads. Written to `notes/menu-widgets.md`.
- [ ] 1.3 Extract the template data and widget assets with `pakmod.py`. Add to `notes/menu-widgets.md`.

## 2. Add a 6th template (question 1)
- [ ] 2.1 Test the run-time Lua route. Written to `notes/template-add.md`.
- [ ] 2.2 Test the pak route. Add to `notes/template-add.md`. Picture evidence in `evidence/` if it works.

## 3. Edit the rows (question 2)
- [ ] 3.1 Test hiding rows (Lua and pak). Written to `notes/rows-edit.md`.
- [ ] 3.2 Test adding a mod row and reading its value in Lua. Add to `notes/rows-edit.md`.

## 4. Setting effects (question 3)
- [ ] 4.1 Map each game setting to the mod code that reads it, or to none. Written to `notes/setting-effects.md`.
- [ ] 4.2 Write the A/B plan per setting (variants, metric, runs, ranges).
- [ ] 4.3 Run the A/B tests for settings that have a possible link. Results to `notes/setting-effects.md`.

## 5. Close
- [ ] 5.1 Restore `menu.sav` and the saves. Check the AES key is not in the diff.
- [ ] 5.2 Write `notes/recommendation.md`: verdict per question and a follow-up change.
- [ ] 5.3 Move lasting engine facts to `docs/wiki/`. Add a `CHANGELOG.md` line if needed.
- [ ] 5.4 Owner decision: ask the owner which follow-up to build (template, rows, keep the separate start menu, or none).
