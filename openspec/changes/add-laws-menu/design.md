## Context

Laws live in `features/tech_tree` (`tech_tree_enact_law`, `tech_tree_repeal_law`, state key `tech_laws`). The tech window had a laws strip and Enact or Repeal buttons on node cards. Menus register through `core/menu.lua` (`menu.register`), as `liege_contracts`, `raid_widget`, `scenario_settings` and `tech_tree_widget` do. The mockup is `mockups/laws-menu.html` (updated by the owner on 2026-11-04).

## Decisions

1. **New feature `laws_menu`.** It registers the menu `laws`, owns the yearly actions, the view and the dialog. The rules (path, node, slot limit) stay in `tech_tree`.
2. **State.** The keys that the enact rule needs live in `tech_tree` (it cannot depend on `laws_menu`): `law_extra_slots` (integer), `laws_unlocked` (dot list of law ids), `laws_sources` (a dot list of pairs: law id, encoded text). ModState keeps only letters, digits, `_`, `.` and `-`, so the source text is encoded (every other byte becomes `_` and two hex digits). The keys of the yearly actions live in `laws_menu`: `laws_year_no` (season counter of the last spring seen, -1 at the start), `laws_enact_used`, `laws_revoke_used`. `laws_menu` opens the shared state without a version (the last version set wins, and it has no migration). A save without the new keys loads with the defaults.
3. **Slots.** Slots = min(`max_total_laws` (5), `max_active_laws` (1) + `law_extra_slots`). `laws_add_slot()` returns `{ slots, added, reason }`; at 5 it changes nothing, `added` is false and `reason` says so.
4. **Unlock sources.** A law is unlocked when its tech node is unlocked, or when `laws_unlock(id, source)` ran (repeat call: no change, `changed = false`). A contract law skips the node and the path rule in `enact_refusal`. The tech tree unlock keeps the path rule. A source text is cut to 120 characters; a missing text shows "Contract".
5. **Yearly actions.** The clock is the one of the tech picks (`tech_tree.spring_season` and the season counter of `invasion.season_info()`). The first look takes the counter and gives the actions at once (a game in any season starts with 1 and 1). Each later start of spring, when the counter is higher, sets both used counters to 0. The counter is saved before the log line, so a load never refreshes twice. A load in spring gives nothing back. The menu checks the actions; the low-level tech commands `tech_tree_enact_law` and `tech_tree_repeal_law` use none (harness use only, since the player has no button for them any more).
6. **Order of refusals.** The yearly action is checked first ("No enact action left this year."), then the slots ("All law slots are used. Revoke a law first."), then the tech rules.
7. **Confirmation dialog.** A click on Enact or Revoke (or the press command) calls `request(kind, id)`: it checks that the action is enabled and keeps `pending = { kind, id }`; nothing else changes. Confirm calls the real action. Cancel and Esc clear `pending`. The base menu gets an optional `on_esc` function: when it returns true the menu used the Esc key (it closed the dialog) and stays open; the next Esc closes the menu. While the dialog is open the card and filter buttons are collapsed, so a click cannot reach them.
8. **View.** A pure function `view.build(model)` returns the header, the nine cards (status, source, effects with a tone, hint, button, enabled) and the dialog model. The effect text uses `tech_tree_widget/lines.effect_line`, the formatter of the tech tooltip. Tones: a gain is green, a loss is red, a neutral effect is grey; a lower buy-back price and a lower banditry order loss are gains (as in the mockup). The filter is view state, not saved.
9. **Widget.** A cooked Widget Blueprint `WBP_Laws`, built by `ue/make_laws_widget.py`: nine pooled cards, a filter row, a dialog on top. The texts of the buttons are text blocks; the click buttons (HarnessClickHooks, never `Button.OnClicked:Add`) lie on top and are invisible (as in the scenario settings window). Colours change with `SetColorAndOpacity` on the text blocks and `SetBrushColor` on Borders. A hidden entry has empty text and a clear brush colour (a collapse does not hold for Borders).
10. **Tech window.** No change to the cooked tech widget. Lua keeps the law buttons and strip buttons hidden, clears the strip texts and shows the line "Laws: open the Laws menu" in the first strip text. The press kinds `law` and `strip` are refused with a message that names the Laws menu. The unused text helpers are removed from `lines.lua`.
11. **Commands.** `InvasionMod.laws_menu_state`, `laws_menu_press` (`action` filter, enact, revoke, confirm, cancel), `laws_menu_open`, `laws_menu_close`, `laws_unlock`, `laws_add_slot`.

## Existing saves over the slot cap

A save made before this change can hold 2 laws in force while the base is now 1 slot. Decision: both laws stay in force until the player revokes one. No law is lost silently. No new enact is possible while the number in force is at or over the slots (the hint says "All law slots are used. Revoke a law first."). The header shows the real count (for example "2 / 1"). One revoke is enough to be under the cap only when the count drops below the slots; here one revoke gives "1 / 1".

## Resolved questions

- Q1 (where enact and revoke live): the Laws menu (owner, 2026-11-04).
- Q2 (cap on slots): 5 in total (owner, 2026-11-04).
- Q3 (cooldown): replaced by 1 enact and 1 revoke for each year (owner, 2026-11-04).
- Q4 (font and panel in the pak): no spike was needed; both were proven in the two style changes.

## Risks

- A pak widget made at run time can crash on `OnClicked:Add`. The menu uses click buttons.
- Two places that show laws can disagree. Both read the one tech tree state.
- A change in the pak is a binary file: two changes that rebuild `InvasionMod_P.pak` conflict at the merge. Rebuild the pak after the merge of `origin/main`.
