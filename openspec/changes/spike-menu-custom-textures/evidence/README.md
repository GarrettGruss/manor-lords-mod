# Evidence: spike menu custom textures

All pictures: test scenario `probe-menu-texture`, run `20261021-033203-e2bb` (verdict pass). Saved as JPEG (quality 72) to stay small. The test PNG is `assets/test_frame.png`: 256x256, parchment, 16 px dark border, red 32 px marker top left.

| Picture | What it shows |
|---|---|
| `png-fullscreen.jpg` | The Image was added with the size override 1280x720 but drew only about 24 px at the top left (a small beige square at the window corner). The size override did not apply at the first frame. |
| `box-small.jpg` | Box (9-slice) brush at 200x200: dark border, sharp square corners, red marker in the corner. |
| `box-wide.jpg` | Box brush at 600x300: same border thickness as at 200x200, sharp corners. The red marker is stretched in x because the marker (32 px) is larger than the 16 px margin. |

Run `20261021-032756-0e6f` (also pass) had the same result, but its pictures show another window in front of the game. Run `20261021-033301-2498` (pass) had another window in front of the game in `png-fullscreen`.
