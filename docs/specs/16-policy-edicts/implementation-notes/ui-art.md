# UI art for the policy menu

Date: 2026-10-14. Tool: `harness/tools/genimage.py` (Gemini API), model `gemini-3.1-flash-image`.

## Result
- 17 policy icons (one per real policy id in `DT_PolicyTypes`: 1 to 4 and 6 to 18) and one menu background panel.
- Committed copies: `mod/PolicyMenu/art/policy_<id>.png` (256 x 256, about 130 KB) and `panel.png` (1024 x 576). Originals (1024 x 1024) stay in `runs/genimage/policy/`.
- Style: one shared prompt (aged parchment, ink outline, manuscript illumination, no text). Subjects per id are in `harness/tools/make_policy_art.py`.
- 19 API calls in total. Icon 11 showed the words "LAND DEED" at first; it was made again with a blank parchment.

## Open
- The icons are not in the widget yet. Next: import them as Texture2D in the UE workspace, set them as button images in `make_widget.py`, cook, pack, and check in the game.
- Some icons are scenes with people (4, 6, 7, 8, 14, 15), the others are single objects. Make the scene ones again as objects if the set must be uniform.
- Models available to the key (2026-10-14): gemini-2.5-flash-image, gemini-3-pro-image(-preview), gemini-3.1-flash-image(-preview), gemini-3.1-flash-lite-image.
