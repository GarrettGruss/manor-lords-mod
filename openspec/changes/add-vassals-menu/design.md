## Context

`mod/vassals` keeps up to 3 slots in ModState (region, lord, policy, flags `stalled` and `rebuilding`, start day) and a separate list of wiped regions (outside the slots). `mod/tribute` pays 2 rich goods each month, `base x policy factor`. Both have state commands. Policies are set only by the command `vassals_set_policy` today. Restore exists as `vassals_restore` (100 silver, region argument). The menu framework is `core/menu.lua`. `liege` is the model for a pak widget with a view module (`features/liege_contracts/view.lua`).

## Decisions

- A new feature folder `features/vassals_menu/` holds the menu code: a pure `view.lua` (text and values, tested in the fake game) and `init.lua` (menu, clicks, commands). The `vassals` and `tribute` features get no menu code. They may export a read function if the state command is too large.
- The widget is `mod/InvasionMod/ue/make_vassals_widget.py`, built like `make_liege_widget.py`, with the controls of the mockup: header, 3 cards, 9 policy buttons, 3 restore buttons. Unused controls are hidden.
- Status: derived from existing flags only (see the spec). No new state is saved.
- A click calls the existing named command. The menu has no path of its own to change state.
- The tribute text of a card uses the tribute rules (`tribute.base`, policy factor, rich goods), not a copy of the numbers.

## Open questions (the owner decides; not decided here)

1. A wiped village has no slot in the code (it is a record outside the slots). The mockup shows it as slot 3. Options: show wiped villages in the free cards, first; or in extra cards. Answered by a fake game test that reads `vassals_state`. Default: wiped villages fill free cards, oldest first.
2. What does an empty slot (never claimed) show? The mockup has no such card. Default: a dim card "Free slot" with the text "Claim and settle a region to gain a vassal", no buttons.
3. The code has no days counter after a restore (the slot starts again). Default: "Vassal for" counts from the new handover.
4. Restore cost and effect: the menu shows the current 100 silver. Should the hint also show the effect (5 families, goods for the rebuild)? Default: the hint shows only the cost.
5. The mockup note for "Rebuilding" shows progress "(0 of 22)". The code has `rebuilt_target` but no public progress value. Default: the note has no numbers.
6. "Thriving" is a new word for "not stalled and not rebuilding". Is the word right?
7. Card order when slot 1 is lost and slot 2 stays: keep slot numbers, or sort by the day of the handover? Default: slot numbers.
8. The mockup shows the rich resource "farmland" and the paid good "flax". The code pays flax as the stand-in for rich soil. Should the card show "farmland" or "flax"? Default: the paid good name.

## Risks

- A pak widget needs a rebuild of the pak. The cooked widget is checked in a real game with pictures.
- A sack or a restore changes state while the menu is open. The menu refreshes by poll while open.
