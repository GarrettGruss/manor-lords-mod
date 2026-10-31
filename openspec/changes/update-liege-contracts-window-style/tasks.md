## 1. Spike

- [ ] 1.1 Find the game's serif font and the dark panel texture; check they load from the pak. Write `notes/fonts-textures.md`, with the fallback chosen.

## 2. Widget

- [ ] 2.1 Rebuild the widget in `make_liege_widget.py` in a private UE workspace and a private pak work_dir.
- [ ] 2.2 Update the view text formatting if needed (capitals, gold, red, "Fulfilled").

## 3. Check

- [ ] 3.1 Run the test scenario `liege-contracts-window`; take screenshots into `evidence/` with a `README.md`.
- [ ] 3.2 Run the fake game tests and `openspec validate update-liege-contracts-window-style --strict`.
- [ ] 3.3 Update `CHANGELOG.md`, the wiki and the skills that the change affects.

## 4. Archive

- [ ] 4.1 Archive as the last commit: `openspec archive update-liege-contracts-window-style --yes`.
