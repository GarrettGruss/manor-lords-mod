# M12: tech-tree

Feature folder: `tech_tree`. Batch 6.

## Goal
Two mutually exclusive paths, oppression and prosperity. Laws, vassal policies and tech nodes are mod-owned. Lua applies the effects. A pak widget shows them.

## Player rules (from M00)
- The tech tree has two exclusive paths. Each path unlocks abilities and passive bonuses.
- Shared manor upgrades (storage, retinue capacity) are in M13.
- First ideas (examples, not decisions):

| | Oppression | Prosperity |
| --- | --- | --- |
| Approval | Higher tolerance for low approval | Approval grows faster. Fewer bandits |
| Bandits | Cheaper to fight. Captured bandits become forced labor | Cheaper to bring back with coin. Returned bandits work at once |
| Vassals | Demand more tribute. Loyalty held by fear | Trade and shared defense. Loyalty held by benefit |
| Liege | Influence from military success | Influence from tribute and wealth |
| Laws | Conscription, forced labor on walls, scorched earth | Militia rights, trade pacts, paying off warbands |
| Defense style | Bulwark and Warband | Pact: buy off, hire against, redirect raids |

- Laws, vassal policies and the tech tree do not use the game's policy system.
- Brief A doctrines (Bulwark, Warband, Pact) give ideas for the nodes.

## Current state
Iterations 01 and 03 are done: `tech_tree` feature with a JSON tree (`mod/InvasionMod/data/tech_tree/tree.json`), path pick, node slots by settlement level, and effects through `bandits` and `unit_balance`. Named commands `tech_tree_state`, `tech_tree_choose_path`, `tech_tree_unlock`. The widget (02) and the laws (04) are open.

## Proven building blocks
- Policy system is not usable (`enactPolicy` false in 95 tries): `openspec/changes/archive/2026-10-15-legacy-16-policy-edicts/README.md`, `implementation-notes/policy-followups.md`, `policies.md`.
- Custom UI from a pak (Widget Blueprint): `openspec/changes/archive/2026-10-15-legacy-16-policy-edicts/implementation-notes/pak-widget-spike.md`, `pak-widget-plan.md`, `policy-menu.md`, `ui-art.md`.
- Pak build and data rows: `openspec/changes/archive/2026-10-15-legacy-09-asset-mods/implementation-notes/pak-spike-findings.md`, `tooling.md`. Skill `harness-pak-mod`.
- Row ids: `openspec/changes/archive/2026-10-15-legacy-23-row-id-range/README.md`. Confirmed block (decision 3): building ids 2200 to 2299. Upgrade ids 117 to 999.
- Tech data tables (`DT_RegionDevelopmentTech`): `docs/mod/M00-invasion-mod/implementation-notes/feasibility-manor-tech-units.md` (read and write test is open).
- Mod state: M01.

## Tunables (M00)
- Node costs and bonuses (M00 gives none; the examples are ideas).
- Cost to undo the path choice, if allowed.

## Dependencies
- M01. M04 (bandit effects). M07 (vassal policies). M08 (tribute effects). M11 (influence effects) is backlog and TBD (decision 9). M13 (manor nodes).
- M05 for the Hussite and army effects.

## Open questions
1. Can the path choice be undone at a high cost, or is it final? (M00 open question 10.)
2. Where does the player pick a node: a pak widget, as in spec 16? Which screen opens it?
3. Which nodes are in version 1? M00 has only examples.
4. Spec 23 bases the id block on the spec number. `feature-breakdown.md` proposes 1000 + 100 times the M number. The user must confirm.
5. Which effects can Lua apply to a region the player does not own? (Same as M07 question 2.)
6. How are laws shown and changed during play?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | path-choice | Choose one of two paths; the choice is kept in mod state. | pass, see [iterations/01-path-choice.md](iterations/01-path-choice.md) |
| 02 | pak-ui | Pak widget that lists nodes and takes the choice. | partial: menu shows the data driven tree (U1 to U4 pass); real mouse clicks not verified, see [iterations/02-pak-ui.md](iterations/02-pak-ui.md) |
| 03 | first-nodes | A few nodes per path with Lua effects. | pass (combined with 01) |
| 04 | laws-and-vassal-policies | Laws and vassal policies. | pass, see [iterations/04-laws-and-vassal-policies.md](iterations/04-laws-and-vassal-policies.md) |
| 05 | laws-menu | The menu lists and toggles the laws. | pass, see [iterations/05-laws-menu.md](iterations/05-laws-menu.md) |

## Follow-up decisions (2026-10-16)
See M00 "User decisions", items 11 to 15. They override the open questions above where they answer them.
- Oppression nodes grant Public Order boons that offset low approval.
- Prosperity nodes boost approval, which removes the Public Order debuff (M04).

## Decisions (2026-10-16, M00 items 22 to 24)
- The 4-node draft per path is approved for now. Path and node choices are final and exclusive.
- Data-driven tree: the feature JSON holds the nodes as a linked list (each node names its next or previous node), plus optional layout data. The mod builds the tree and the menu from it. No hard-coded tree unless a technical limit forces it.
- Cost: free. One node slot unlocks each time the settlement level rises.
- Schema form (user, 2026-10-16): each node lists the node ids it `requires` (a linked form that also allows branches). Fields: id, path, name, effect, requires, layout. Write the full schema in iteration 01.

## Boon sizes (M00 decision 29, 2026-10-17)
TBD, tuned in playtests. The agent chose the numbers marked with an asterisk.
| Node | Boon |
| --- | --- |
| Martial Law | Public Order +10 |
| Iron Hand | Public Order +15, buy-back cost +25%* |
| Veteran Levies | militia defence +10%* |
| Fear of the Lord | Public Order +25 while garrison >= 4 squads* |
| Fair Courts | approval +5 |
| Amnesty | buy-back cost -50% |
| Militia Rights | militia attack +10%* |
| Golden Age | approval +15 |
