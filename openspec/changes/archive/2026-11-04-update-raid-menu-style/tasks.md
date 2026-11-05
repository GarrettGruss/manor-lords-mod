## 1. Widget

- [x] 1.1 Rebuild `WBP_RaidMenu` in `make_raid_widget.py` in a private UE workspace and a private pak work_dir: font, flat panel, title and rule, info line, five rows with marker and separator, no close bar.
- [x] 1.2 Update `raid_widget/init.lua` (and `lines.lua` if needed): split each line into label and value, gold values, collapse an empty row.
- [x] 1.3 Fake-game tests: `raid_widget_state` still returns the full lines; the label and value split; an empty line collapses.

## 2. Pak

- [x] 2.1 Rebuild the pak `InvasionMod_P.pak`. Before the commit, grep the diff for the AES key (never print it).

## 3. Check

- [x] 3.1 Run `mod/InvasionMod/scenarios/invasion/raid_widget.py` in the real game, in slot 1 or 2 by number (never `--slot auto`; check the slot in the `config.json` of the run). Take screenshots with `ctx.screenshot` into `evidence/` (at most 1280x720, about 1 MB in all) with `README.md`: run id, test scenario, and the commit SHA. Show the menu with a planned raid and with a switched-off raid type.
- [x] 3.2 Run the full test set and `openspec validate update-raid-menu-style --strict`.
- [x] 3.3 Update `CHANGELOG.md` (Unreleased, Changed), the wiki and the skills that the change affects. Run `wiki.py check`.

## 4. Archive

- [x] 4.1 Archive as the last commit: `openspec archive update-raid-menu-style --yes`.
