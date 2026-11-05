## Why

<!-- Issue: #563 -->

Laws are enacted and repealed inside the tech tree window today. The player has no place that shows all nine laws, how to unlock each one, and what each one does. Contracts will later give laws and law slots as rewards. The owner approved a dedicated Laws menu (2026-11-04). Issue: #563. On 2026-11-04 the owner also decided the open questions and added rules (see "Owner decisions").

## What Changes

- A new menu "Laws" (menu id `laws`) with a button on the bottom bar, like the other mod menus.
- A header: "Laws in force: N / S (max 5)", "Enact this year: N / 1", "Revoke this year: N / 1", the unlocked count, the line "Enact and revoke actions refresh in spring, in N days.", and a filter All, Unlocked, Locked.
- One card for each of the nine laws of `tree.json`: name, status (In force, Unlocked, Locked), "Unlocked by" (a tech tree node, or a contract reward), every effect with a sign colour, a hint line and an Enact or Revoke button. Locked cards show how to unlock.
- Enact and revoke move from the tech window to the Laws menu. The tech window keeps unlocking and shows "Laws: open the Laws menu".
- Every enact and revoke asks for a confirmation dialog first. Nothing changes until the player confirms.
- Law slots: 1 base slot (was 2), at most 5 in total with the extra slots of contracts.
- 1 enact action and 1 revoke action for each game year, refreshed at the start of spring. They are saved in mod state.
- Two entry points for the future contracts change: `laws_unlock(id, source)` and `laws_add_slot()`, with named commands. A law won from a contract works whatever the tech path.
- Game-menu style: font `/Game/UWG/fonts/CombinedFont_Mikadan`, flat dark grey panel, the framework's bottom Close (as in `update-liege-contracts-window-style` and `update-scenario-settings-window-style`).
- The widget is a new cooked asset, built by `mod/InvasionMod/ue/make_laws_widget.py`.
- Mockup (reference, updated 2026-11-04): `mockups/laws-menu.html`.

## Owner decisions (2026-11-04)

1. Q1 yes: enact and revoke move to the Laws menu.
2. 1 base slot, at most 5 in total. `laws_add_slot()` does nothing past 5 and returns a clear result (the contracts change will give a fallback reward).
3. 1 enact and 1 revoke for each year, refreshed in spring (the clock of the tech picks). Used counters show red. Buttons are disabled with "No enact action left this year." or "No revoke action left this year.".
4. A law from a contract (`laws_unlock(id, "contract")`) works whatever the tech path. The path rule stays for tech tree unlocks only.
5. A confirmation dialog for every enact and revoke.
6. Q2 (cap on slots) is decided by 2. Q3 (cooldown) is replaced by the yearly actions.

## Design pillars

Serves `design/mod/invasion-mod.md` pillar 6 (one path of rule) and decision 2 (laws are mod-owned). Laws stay free of cost, limited by slots and by the yearly actions, and path laws stay exclusive to their path in the tech tree. The menu adds no new law effect. It does not break a pillar.

## Non-goals

- No new laws and no change of law effects or values.
- No contracts that give laws or slots. A later change calls the entry points (and the fallback reward at the slot cap).
- No change of the tech picks, paths or vassal policies.

## Impact

- New spec: `mod/laws_menu`.
- Modified specs: `mod/tech_tree` (slots, unlock source, contract unlock), `mod/tech_tree_widget` (law actions move).
- Code (gate 2): a new feature `laws_menu` in `mod/InvasionMod/Scripts/features/`, `mod/InvasionMod/ue/make_laws_widget.py`, changes in `tech_tree` (state, slots) and the tech widget Lua, the base menu option `on_esc`.
- Existing saves: a save with 2 laws in force and the new base of 1 keeps both laws (see design).
