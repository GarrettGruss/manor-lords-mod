## Why

<!-- Issue: #591 -->

The owner decided on 2026-11-06 to give the Large liege contracts one more reward that the player can use at once and keeps: a new retinue squad. The squad starts with 5 men and the player grows it with the normal retinue recruiting. The owner also found two faults in the loan cost of a Large contract: it can take a militia or levy squad (it must take a retinue squad only), and a 5-man retinue squad was logged as `spearMilitia`. The player also gets no notice when a loaned squad returns. Issue: #591.

## What Changes

- **New reward kind `retinue_squad`** in the Large reward pool: "+1 retinue squad". It adds one native retinue squad with 5 men (spike result: `notes/spike-native-retinue.md`). The game saves it. The mod pays the 5 men; the player pays the normal silver (50 for each man) to recruit more.
- **Cap of 4** retinue squads from contracts (owner decision 2026-11-06). At the cap the reward is not drawn, and if it is fulfilled at the cap it pays King's Favour (the rule of `law_slot`).
- **The loan cost takes a retinue squad only** (never militia or levy). With no retinue squad the contract cannot be fulfilled and the card says "Needs a retinue squad". With more than one retinue squad the smallest is loaned (an owner question). A loaned retinue squad returns as a native retinue squad with the same number of men. The wrong detection as `spearMilitia` is removed.
- **A banner when a loan ends**: "The liege returns your squad (5 men)" (`ManorCore.show_banner`).
- Data: `contracts.json` gets the reward row. Config: `retinue_squad_men` (5) and `retinue_squad_cap` (4).
- A helper in the feature manor_stronghold adds a native retinue squad (`retinue.add_native_squad(men)`); the feature liege_contracts calls it.

## Design pillars

Serves `design/mod/invasion-mod.md` pillar 2 (rule through others: the liege pays with soldiers and asks for soldiers) and keeps pillar 3 (the squad is small; growing it costs silver).

## Non-goals

- No change of the other rewards, costs, limits, offers or the window layout.
- No squad above the native limit of 12 men for each native retinue squad. (The mod squads of manor_stronghold, 36 men, are unchanged.)
- No save call in the feature. The game saves the native squad.

## Open questions for the owner

1. Native recruiting stops at 12 men for each squad (a code limit). The owner expected growth to 36. Is 12 enough, or should the mod add a hire path above 12?
2. With two or more retinue squads the loan takes the smallest. Is that right?

## Impact

- Modified specs: `mod/liege_contracts`, `mod/manor_stronghold`.
- Data: `mod/InvasionMod/data/liege_contracts/contracts.json`.
- Code (gate 2): `features/liege_contracts/` (`loader.lua`, `rules.lua`, `view.lua`, `world.lua`, `init.lua`), `features/manor_stronghold/retinue.lua`, `Scripts/config.lua`.
