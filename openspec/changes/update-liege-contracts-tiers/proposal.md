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
- Two tables (requests and rewards by tier) are in `design.md`. All amounts are proposed defaults that the owner tunes in config.

## Non-goals

- No change of the influence rules outside contracts, and no new use of influence.
- No new reward kinds beyond the ones listed. No contracts that need fighting, building or public order.
- No change to `design/mod/`. The owner writes the game design.
- No new art. The window uses the controls of the existing pak where possible (see design, risks).

## Open questions (for the owner; not decided here)

1. The arms shipment button now sits in the footer of the contracts window. The new mockup has no footer text and a bottom bar with only a Close button. Where does the arms shipment button go (another window, the top bar, or removed)?
2. Which goods count as "tier 1" and which as "tier 2"? Proposal: tier 1 = raw goods, tier 2 = produced goods (see design).
3. May a delivery use goods from any store of the player region, or only the manor storage? Default in this draft: what the current feature does (any store of the player region, tier 1 stores first, then tier 2 stores).
4. Regional wealth: no safe write path is proven for our mod (see design, risks). A spike is needed, or the Small reward drops to goods only.

## Impact

- Spec: `mod/liege_contracts` (delta in this change). `mod/liege_influence` needs a small delta once question 1 is answered (the arms shipment button).
- Code (later, gate 2): `mod/InvasionMod/Scripts/features/liege_contracts/*.lua`, `data/liege_contracts/contracts.json`, the liege menu pak widget, `Scripts/config.lua`, the tests and test scenarios of the feature.
- Old saves: the keys `contracts_active`, `contracts_start_day`, `contracts_baseline` and `contracts_progress` are dropped. An old offer is dropped.
