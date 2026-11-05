## Context

`mod/vassals` keeps up to 3 slots in ModState (region, lord, policy, flags `stalled` and `rebuilding`, start day) and a separate list of wiped regions (outside the slots). `mod/tribute` pays 2 rich goods each month, `base x policy factor`. Both have state commands. Policies are set only by the command `vassals_set_policy` today. Restore exists as `vassals_restore` (100 silver, region argument). The menu framework is `core/menu.lua`. `liege` is the model for a pak widget with a view module (`features/liege_contracts/view.lua`).

## Decisions

- A new feature folder `features/vassals_menu/` holds the menu code: a pure `view.lua` (text and values, tested in the fake game) and `init.lua` (menu, clicks, commands). The `vassals` and `tribute` features get no menu code. They may export a read function if the state command is too large.
- The widget is `mod/InvasionMod/ue/make_vassals_widget.py`, built like `make_liege_widget.py`, with the controls of the mockup: header, 3 cards, 9 policy buttons, 3 restore buttons. Unused controls are hidden.
- Status: derived from existing flags only (see the spec). No new state is saved.
- A click calls the existing named command. The menu has no path of its own to change state.
- The tribute text of a card uses the tribute rules (`tribute.base`, policy factor, rich goods), not a copy of the numbers.

## Decisions of the owner (2026-11-04)

The owner accepted all 8 defaults of the open questions.

1. Wiped villages fill the free cards, oldest first. A wiped village has no slot in the code (it is a record outside the slots). A free card shows the oldest wiped record that is not shown yet. If there are more records than free cards, the oldest ones show.
2. A slot that was never claimed shows a dim card "Free slot" with the text "Claim and settle a region to gain a vassal." and no buttons.
3. "Vassal for" counts the days from the new handover after a restore (the slot starts again).
4. The restore hint shows only the cost: "Costs 100 silver." (or "Needs 100 silver." when the silver is lower). It does not describe the effect.
5. The note for "Rebuilding" has no progress numbers ("No tribute until the village is rebuilt.").
6. "Thriving" means a handed-over vassal that is not stalled and not rebuilding.
7. Cards stay in slot order. A lost slot does not move the other cards.
8. A region with rich soil shows the paid good "flax" (the tribute rules use flax as the stand-in). The card shows the names of the paid goods in "Rich resources".

Small additions of the build that the decisions do not cover (no new rule, only what the card must show):
- A vassal that is registered but not yet handed over to a lord has the status "Claimed", "No lord yet" and the tribute "none" (the tribute tick also skips it). The status list of the spec has no word for it.
- The widget has a note line for each card. A refused click shows the reason in this line for 6 s (`vassals_menu.notice_s`).
- The click calls the command through the command layer (`HarnessCommands.dispatch`), so the menu and a test command run the same code.

## Risks

- A pak widget needs a rebuild of the pak. The cooked widget is checked in a real game with pictures.
- A sack or a restore changes state while the menu is open. The menu refreshes by poll while open.
