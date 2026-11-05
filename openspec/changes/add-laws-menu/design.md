## Context

Laws live in `features/tech_tree` (`tech_tree_enact_law`, `tech_tree_repeal_law`, state key `tech_laws`, limit `config.tech_tree.max_active_laws` = 2). The tech window has a laws strip and Enact or Repeal buttons on node cards. Menus register through `core/menu.lua` (`menu.register`), as `liege_contracts`, `raid_widget`, `scenario_settings` and `tech_tree_widget` do. The mockup is `mockups/laws-menu.html`.

## Decisions

1. **New feature `laws_menu`.** It registers the menu `laws` and builds the view from the tech tree state. It keeps only the extra slots and the contract unlocks (see 3 and 4).
2. **Reuse the law functions.** Enact and Revoke call the existing tech tree functions, so the rules (path, slot limit, locked) stay in one place. The key `tech_laws` is unchanged. A save made before this change loads as it is.
3. **Unlock sources.** A law is unlocked when its tech tree node is unlocked, or when `laws_unlock(id, source)` ran. Contract unlocks are kept in new mod state keys `laws_unlocked` (comma list of ids) and `laws_sources` (the source text, for the "Unlocked by" line). `source` is a short text such as "Contract: Grain for the Liege". A path law of the other path stays refused, also when a contract unlocked it.
4. **Slots.** Slots = `max_active_laws` + `law_extra_slots` (new state key, integer, default 0). `laws_add_slot()` adds 1 and returns the new total. No cap yet (Q2).
5. **Entry points.** `laws_unlock(id, source)` and `laws_add_slot()` are Lua functions of the feature and named commands `InvasionMod.laws_unlock` and `InvasionMod.laws_add_slot`. The contracts change calls the functions. A repeat call for the same law changes nothing.
6. **View.** A pure function `laws_view(state)` returns the header and nine cards (name, status, unlocked_by, effects with sign, button text, enabled flag, reason). It is tested without the game. Effect text uses the same formatter as the tech tooltip, so the values match.
7. **Widget.** A cooked Widget Blueprint `WBP_Laws`, built by `ue/make_laws_widget.py` from the mockup layout, with nine pooled cards and a filter row. The filter is view state, not saved. Buttons are attached in `on_open` as in the liege menu (never `OnClicked:Add` on a button made at run time: DANGEROUS_ACTIONS.md).
8. **Commands for tests.** `InvasionMod.laws_menu_state` and `laws_menu_press`, like the tech widget press command.

## Open questions

- **Q1 (owner): where do enact and revoke live?** Recommendation: the tech window keeps unlocking (picks, nodes, common techs). The Laws menu does enact and revoke. The tech window drops its Enact and Repeal buttons and the laws strip, and shows one line "Laws: open the Laws menu". Reason: one place for law choices, and contract laws have no node in the tech window. Alternative: both places work. The delta spec follows the recommendation; the owner may reverse it before gate 2.
- **Q2 (owner): cap on extra law slots.** Not decided. This spec has no cap. Decide before the contracts change.
- **Q3 (owner): cooldown for swapping laws.** Not decided. This spec has no cooldown.
- **Q4: font and panel in the pak.** Both were proven in the two style changes (their `notes/`). No spike expected.

## Risks

- A pak widget made at run time can crash on `OnClicked:Add`. Follow the liege menu way.
- Two places that show laws can disagree. Both read the one tech tree state.
