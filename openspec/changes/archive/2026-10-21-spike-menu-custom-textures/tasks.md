## 1. Spike
- [x] 1.1 Candidate 2: load a test PNG at run time and show it in a mod menu `Image`; verify with a real game run and a screenshot. Write `notes/runtime-png.md`.
- [x] 1.2 Candidate 1: cook a test texture into a test pak and show it in a mod menu `Image`; verify with a real game run and a screenshot. Write `notes/pak-texture.md`. Not done: not needed after the owner decision (notes/pak-texture.md).
- [x] 1.3 Draw a frame texture as Box (9-slice) at two sizes; verify with a screenshot that the corners stay sharp. Add to the note of the way that worked.
- [x] 1.4 Try a custom font from a pak on a `TextBlock`; verify with a screenshot, or record why it fails. Write `notes/custom-font.md`. Not tried: needs an editor cook (notes/custom-font.md); the game fonts are used for now.
- [x] 1.5 Recommend one way for the base menu of #308 and the Book of Charters menu; write `notes/recommendation.md`, and ask the owner.

## 2. Close
- [x] 2.1 Move lasting engine facts to the wiki (UI and menus page) and add a `CHANGELOG.md` line if a tool or pak changed.
- [x] 2.2 Owner decision (2026-10-21): approved. Menus may use PNG images loaded at run time (ImportFileAsTexture2D, SetBrushFromTexture, 9-slice). Answers the owner question of notes/recommendation.md.
