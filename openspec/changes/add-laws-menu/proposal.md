## Why

<!-- Issue: #563 -->

Laws are enacted and repealed inside the tech tree window today. The player has no place that shows all nine laws, how to unlock each one, and what each one does. Contracts will later give laws and law slots as rewards. The owner approved a dedicated Laws menu (2026-11-04). Issue: #563.

## What Changes

- A new menu "Laws" (menu id `laws`) with a button on the bottom bar, like the other mod menus.
- A header: laws in force against slots (2 base slots plus extra slots), the unlocked count, and a filter All, Unlocked, Locked.
- One card for each of the nine laws of `tree.json`: name, status (In force, Unlocked, Locked), "Unlocked by" (a tech tree node, or a contract reward), every effect with a sign colour, and an Enact or Revoke button. Locked cards show how to unlock.
- Enact is disabled with the text "All law slots are used. Revoke a law first." when all slots are used.
- Two entry points for the future contracts change: `laws_unlock(id, source)` and `laws_add_slot()`, with named commands.
- Law slots become `max_active_laws` plus extra slots. Extra slots are saved in mod state.
- Enact and Revoke act at once and are saved in mod state, with the existing law keys.
- Game-menu style: font `/Game/UWG/fonts/CombinedFont_Mikadan`, flat dark grey panel, the framework's bottom Close (as in `update-liege-contracts-window-style` and `update-scenario-settings-window-style`).
- The widget is a new cooked asset, built by a script in `mod/InvasionMod/ue/` (as `WBP_LiegeContracts`).
- Mockup (reference): `mockups/laws-menu.html`.

## Design pillars

Serves `design/mod/invasion-mod.md` pillar 6 (one path of rule) and decision 2 (laws are mod-owned). Laws stay free, limited by slots, and path laws stay exclusive to their path. The menu adds no new law effect. It does not break a pillar.

## Non-goals

- No new laws and no change of law effects or values.
- No contracts that give laws or slots. A later change calls the entry points.
- No cap or cooldown for law changes (open questions).
- No change of the tech picks, paths or vassal policies.

## Impact

- New spec: `mod/laws_menu`.
- Modified specs: `mod/tech_tree` (slots, unlock source), `mod/tech_tree_widget` (law actions move, see design).
- Code (gate 2): a new feature `laws_menu` in `mod/InvasionMod/Scripts/features/`, `mod/InvasionMod/ue/make_laws_widget.py`, small changes in `tech_tree/init.lua` and the tech widget.
