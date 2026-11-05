## Context

This change is visual only. The five line texts, the refresh, F8, the commands and the pak name do not change. The mockup `mockups/raid-menu-game-style.html` is the visual source. It uses Alegreya as a stand-in for the game font.

## Decisions

- **Reuse the approach of the two archived changes.** Font: `/Game/UWG/fonts/CombinedFont_Mikadan` (a stub asset at the game path in the editor workspace, never shipped). Panel: flat dark grey colour, no texture. Background: flat near-black. Read `notes/fonts-textures.md` of `update-liege-contracts-window-style`. Do not repeat its spike.
- **Colours:** gold #e8c87a, white text, grey labels, rule #9c8455. A `LinearColor` is linear: convert the sRGB values (`v ** 2.2`).
- **Rows:** each of the five lines becomes a row of two text blocks (label, value) and a diamond marker. `RaidLine<i>` keeps its name and shows the value part. A new `RaidLabel<i>` shows the label. Lua splits the line at the first ": ". The shown and wanted lines in `raid_widget_state` stay the full line, so the existing tests do not change.
- **Gold values:** numbers and key words in a value are gold. If one text block cannot hold two colours, the value block is gold as a whole. Choose in gate 2 and say it in the pull request.
- **Empty line:** the row (marker, texts, separator) is collapsed with `SetVisibility`, not left as a blank row.
- **Title and info line:** `TitleText` shows "RAIDS". The info line reuses the difficulty line (`Raid levels: ...`) with gold numbers. It stays one of the five lines in the state.
- **Close:** the framework makes the bottom Close (`core/menu.lua`). The widget has no close bar or button. The menu registers as before.
- **Known pitfall:** a Border paints white by default. Set `brush_color` alpha 0 on every Border that must be clear (as the difficulty slots do today). Do not rely on Border underline colouring: use a thin Border as the rule.

## Risks

- A game font may not load from the pak. The fallback of the liege change applies (engine font, same layout).
- Gold in one text block needs rich text or several blocks. Keep the widget count small.
- A wrong build step can install the old pak (the trap in `notes/fonts-textures.md` of the liege change). Check for the log line `built ...InvasionMod_P.pak` before a run.
