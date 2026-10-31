# Fonts and textures for the liege window (task 1.1)

## Result
- Font: **the game font works.** `/Game/UWG/fonts/CombinedFont_Mikadan` (the font of the game's Close button and most of its UI, found in `menuButton.uasset`) is used by every text block of the widget. The Fulfil label is the exception: it belongs to `WBP_ClickButton` and keeps its own sans font.
- Panel texture: **not used.** `/Game/UWG/ui_textures/grungeTiling` (used by the Diplomacy letter screen) loads from the pak widget, but it is almost black. Even with a bright tint it only gives a dark panel, not the dark grey of the mockup. The panel is a flat colour (fallback of design.md). No rough edge.
- Soft centre light: not done. The background is a flat near-black Border (open question 3 of design.md: flat is enough).

## How a pak widget references a game asset
The editor workspace has no game content. `make_liege_widget.py` makes an empty stub asset at the game path (`unreal.Font` with `FontFactory`, saved), sets it as `font_object` of each text, and the cook writes only the path. Copy only `WBP_LiegeContracts.*` into the pak: the stub is never shipped, and the game loads its own asset by path. The result is proven by the game screenshots (evidence/), not by the cooked file.
- The font path and the texture path are read from the environment (`LIEGE_FONT`, `LIEGE_TEXTURE`, `LIEGE_TYPEFACE`) with the default Mikadan font. Pass them without a leading slash: Git Bash rewrites `/Game/...` (the script adds the slash).
- Font candidates seen in the game paks: `Goudy_Mediaeval_DemiBold_Font` (NotStronghold/Fonts, an offline font with a texture page; it fell back to the engine sans in the game), `favarotta_italic_Font`, `GermaniaOne-Regular_Font`, the Saira fonts (sans), `CombinedFont_Mikadan` (composite: Mikadan_Regular, favarotta_italic, arial-unicode-ms).
- Default typeface name of the composite font works (no `typeface_font_name` needed).

## Traps
- `pakmod.py --config` needs a Windows path (`C:/...`) for the config file when `MSYS_NO_PATHCONV=1` is set. With a POSIX path the build step fails, and the run then installs the OLD pak from the private work folder (several runs of the spike showed invisible text because of that: run ids 20261031-174545-6584 to -175552-1c6a are void). Check that the log line `built ...InvasionMod_P.pak` appears before a run.
- A `LinearColor` is linear: the sRGB values of the mockup must be converted (`v ** 2.2`), otherwise the dark colours show 0.26 grey.
- Button look: the Fulfil label stays the click button's own text. The box is removed at run time: `Button01:SetBackgroundColor` with alpha 0 and `SetBrushColor` alpha 0 on its TextBorder (child 1, the label's parent, the same path `bind_texts` uses).
- Dimming a card: `Border:SetRenderOpacity(0.45)` on the card Border (a plain float call).

## Runs
Final runs: 20261031-181104-160e (manor), 20261031-181238-0056 (no manor), 20261031-181329-ef69 (`liege-contracts-fulfil`), 20261031-180913-2893 (`liege-contracts-new-game-offer`), 20261031-182153-f2ae (window, final Lua). All pass, slot 1, no crash.
