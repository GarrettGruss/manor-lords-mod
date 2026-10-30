## Why

The owner (decision of 2026-10-30) wants simpler and more regular liege contracts. Today the liege offers 3 contracts a year, the player picks one, and a missed deadline costs 500 influence. The new design offers 9 contracts a year in three tiers. All of them are deliveries of goods. The player fulfils them at will and no contract has a penalty.

Issue: #TBD (the issue `Change: update-liege-contracts-tiers` is made after the owner reviews this draft).

This change serves the pillar "the liege expects duty" and pillar 3 "scarcity forces expansion" of `design/mod/invasion-mod.md`: the goods the liege asks for compete with the needs of the town. It does not break a pillar. It continues the archived change `update-liege-tribute-to-contracts` (#505). It does not continue a legacy doc folder.

## What changes

- Each spring the liege offers 9 contracts: 3 random contracts from each of the tiers Small, Medium and Large.
- The player may fulfil at most N contracts per tier per year. N is a config value per tier (default 1).
- Contracts expire when winter begins. There is NO penalty (the config value `fail_penalty` and the -500 influence rule are removed). New contracts come in spring.
- A request is a delivery of goods only. The objective kinds `build_count`, `kill_raiders`, `hold_public_order` and `raise_militia_squads` are removed.
- There is no pick step and no active contract. Each card has a "Fulfil" button. It is enabled only when the goods are in the player's storage and the tier limit is not reached. A click takes the goods and pays the reward at once.
- One reward for each contract, by tier: Small = tier 1 goods or regional wealth; Medium = weapons, tier 2 goods or treasury silver; Large = 1 tech point or 1000 influence.
- New liege window, as in the mockup `mockups/liege-contracts-tiers.html`: three rows (one for each tier) of three cards, a top bar with two countdowns, and a full-width Close button at the bottom.
- A request asks for one good of the tier. The goods tiers are the owner's lists of 2026-10-30 (see `design.md`): Small asks for tier 1 goods, Medium for tier 2 goods, Large for tier 3 goods (the lead's default; the owner may change it).
- The request amount is `round(base(tier) * weight(good) * difficulty)`, at least 1. Base, weight and difficulty are config values.
- Two tables (requests and rewards by tier) are in `design.md`. All numbers are proposed defaults that the owner tunes in config.

## Non-goals

- No change of the influence rules outside contracts, and no new use of influence.
- No new reward kinds beyond the ones listed. No contracts that need fighting, building or public order.
- No change to `design/mod/`. The owner writes the game design.
- No new art. The window uses the controls of the existing pak where possible (see design, risks).

## Decided by the owner (2026-10-30)

- The arms shipment button moves to the manor (the manor building's menu or panel). It leaves the contracts window.
- A delivery may take goods from any storehouse of the player region (as today).
- 1000 influence for a Large contract is intended.

## Open questions (for the owner; not decided here)

1. Regional wealth: no safe write path is proven for our mod (see design, risks). A spike is needed, or the Small reward drops to goods only.
2. Difficulty: the lead assumes it comes from the yearly raid level in the scenario settings (1 easy 0.75, 2 medium 1.0, 3 hard 1.25, 0 off 1.0). Is that the right source and are those values right?
3. The assumption that a Small contract asks for tier 1 goods, Medium for tier 2 and Large for tier 3. Is that right?

## Impact

- Spec: `mod/liege_contracts` (delta in this change). `mod/liege_influence` has a delta in this change (the arms shipment button moves to the manor).
- Code (later, gate 2): `mod/InvasionMod/Scripts/features/liege_contracts/*.lua`, `data/liege_contracts/contracts.json`, the liege menu pak widget, `Scripts/config.lua`, the tests and test scenarios of the feature.
- Old saves: the keys `contracts_active`, `contracts_start_day`, `contracts_baseline` and `contracts_progress` are dropped. An old offer is dropped.
