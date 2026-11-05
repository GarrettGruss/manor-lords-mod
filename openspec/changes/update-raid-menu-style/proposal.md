## Why

<!-- Issue: #562 -->

The Hussites menu (the raid menu, widget `WBP_RaidMenu`, menu id `raid`) still has the old look: a brown panel with plain text lines. The liege contracts window and the scenario settings window were restyled to the game-menu style (changes `update-liege-contracts-window-style`, #538, and `update-scenario-settings-window-style`, #540). The owner reported on 2026-11-04 that the raid menu must match them. Issue: #562.

## What Changes

- Restyle the raid menu to the mockup `mockups/raid-menu-game-style.html`.
- Game font `/Game/UWG/fonts/CombinedFont_Mikadan` for all text.
- Flat dark grey panel (the texture `grungeTiling` is too dark), on a near-black background.
- Title "RAIDS" in capitals with a thin gold rule.
- One info line below the title with gold values (the difficulty levels line).
- The raid lines are rows with a diamond marker and a thin separator. The label is light grey, the value is white, and numbers and key words are gold (#e8c87a).
- A line that is empty (a switched-off raid type) shows no row.
- The only Close is the framework's game-style bottom Close. There is no extra close bar in the widget.
- Content and behavior do not change: the five lines, their texts, the order, the refresh, F8 and the commands stay as they are.

## Impact

- Spec: `mod/raid_widget`. ADDED: "The menu follows the approved look" (the living spec has no look requirement yet). The behavior requirements are not changed. The mockup moves to `openspec/specs/mod/raid_widget/mockups/` at the archive.
- Code (gate 2): `mod/InvasionMod/ue/make_raid_widget.py`, the pak widget, `Scripts/features/raid_widget/init.lua` (colour and text split), and `lines.lua` if a helper that splits a line into label and value is needed.
- Dependency: the font and panel result of the liege restyle (`notes/fonts-textures.md`, archived). Reuse it.
