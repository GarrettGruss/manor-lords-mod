## Why

<!-- Issue: #538 -->

The liege contracts window uses a beige panel. The game's own Diplomacy and Help Subjects windows look different: dark, quiet and serif. The owner approved a mockup in the game style (decision 2026-10-31). The window should match the game. Issue: #538.

## What Changes

- Restyle the liege window (menu id `liege`) to the mockup `mockups/liege-contracts-game-style.html`.
- Near-black background with a soft centre light, no beige panel.
- Centred title in spaced small capitals with a thin gold rule, and one countdown line with gold numbers (#e8c87a).
- One dark grey panel with rough edges holds the three tier rows and nine cards.
- White serif card text, diamond markers, goods and rewards in gold capitals, a missing amount in muted red.
- Fulfil is plain serif text, not a boxed button. Disabled cards are dimmed. A fulfilled card shows a gold "Fulfilled".
- The only Close is the framework's bottom-centre Close. No Close inside the widget.
- Behavior does not change: tiers, formula, manor check, notice line and countdowns stay as they are.

## Impact

- Spec: `mod/liege_contracts`, requirement "The liege window shows contracts by tier" (MODIFIED).
- Code (gate 2): `mod/InvasionMod/ue/make_liege_widget.py`, the pak widget, and the view text format if needed.
