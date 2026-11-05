## Why

<!-- Issue: #564 -->

The player rules vassals only through policies and restore orders. Today this works only through commands. The owner asked for a Vassals menu in the game (2026-11-04), with a mockup (`mockups/vassals-menu.html`). Issue: #564.

Design: the menu serves pillar 2 ("rule through others: vassals only by policies and orders") and pillar 3 ("scarcity forces expansion: vassals supply") of `design/mod/invasion-mod.md`. It shows what vassals pay and offers only the existing controls: the policy and the restore of a wiped village. It adds no new control over a lord, so it keeps all pillars.

## What Changes

- New menu `vassals` ("Vassals") in the bottom bar, in the game-menu style of `liege` and `scenario_settings` (changes `update-liege-contracts-window-style`, `update-scenario-settings-window-style`).
- Header: vassals N / 3, total tribute each month (goods summed over the vassals that pay), treasury silver.
- One card for each vassal slot (3): region, lord, status, rich resources, tribute each month, families, buildings, days as vassal, a note line, policy buttons Light, Fair and Heavy with a hint line.
- A wiped village shows a button "Restore the village" (100 silver). It calls the existing command `InvasionMod.vassals_restore`.
- The data comes from the existing state commands `vassals_state` and `tribute_state`. A policy click calls the existing `vassals_set_policy`.
- The widget is a new cooked pak asset, built by `mod/InvasionMod/ue/make_vassals_widget.py` (like `make_liege_widget.py`).
- Open questions (not decided here): see `design.md`.

## Non-goals

- No new restore mechanics. The cost, the effect and the rules stay as in `mod/vassals`.
- No new status logic. A status that the code does not have is an open question.
- No new policies, no change of the tribute amounts, no order for a lord.
- No save call. The menu only reads state and calls existing commands.

## Impact

- New spec: `mod/vassals_menu`.
- Code (gate 2): new feature folder `mod/InvasionMod/Scripts/features/vassals_menu/`, `mod/InvasionMod/ue/make_vassals_widget.py`, the pak widget, a fake game test, a test scenario.
- Legacy docs: none. Continues `mod/vassals` and `mod/tribute`.
