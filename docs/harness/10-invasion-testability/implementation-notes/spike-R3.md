# Spike R3: loot on the ground

Date: 2026-10-10. Branch `feat/27-sack-primitives`. Follows `spike-S5.md` (no ground object after a death).
Verdict: **the base game has no ground loot.** The test method is verified on a stand-in ledger (`HarnessLoot`). A pile on the ground and a walking peasant are not verified: the mod must define them.

## What was tried
| Try | Result |
|---|---|
| Search the jmap dump of the game for classes and functions named pile, loot, drop, dropped, stockpile, pickup, plunder, spoils | nothing in `/Script/ManorLords` or `/Game/CPP_BP`. The only hits are `ItemsLooted` (a property of `SMUnit`) and unrelated ground cover and board functions. |
| Kill carriers and compare the actor classes (spike S5) | no new actor class, no change in any count. `ItemsLooted` is cleared on death. |
| `Region.corpses` after a death | holds the dead unit (a dead ox appeared), no goods. |
| Building types with a pile idea (`EBuildingType`) | `Supplies` (88) is the nearest thing: a crate that holds goods. It is a building, so it can only be placed with the OS mouse (`place_building`). Not used. |
| `AddItemToBuilding` (cheat) | no effect (see `spike-S6.md`). |
| `GiveItemByID` / `GiveItemByName` | adds goods to a store with space. This is the "recover" half. |
| Spawn a goods actor from Lua | no class found to spawn. Not tried. |

## The stand-in ledger (`mod/shared/HarnessLoot`, commands `drop_loot`, `loot_piles`, `recover_loot`)
- `drop_loot(count, good, side)` takes up to `count` live units of one side that carry loot (`ItemsLooted > 0`), records a pile for each (id, x, y from `realPos`, amount = `ItemsLooted`, good), and kills the unit with `just_die`.
- `loot_piles()` lists the piles. `recover_loot(pile)` adds the amount of the pile to the stock (`MLCheatManager:GiveItemByID`) and removes the pile. An unknown pile is refused.
- The piles are Lua tables in the state of `HarnessActions`. They are not objects in the world. A recovery is instant: no peasant walks.
- Limits: at most 50 piles, `good` 1 to 1000, `count` 1 to 50, side one of player, ai, bandit, civil.

## Scenario `loot-drop-recovery` (COVERS R3)
Spawns a raid (+18 units), puts 7 loot on 3 bandits (read back 21), `drop_loot(3, Planks)`: 3 piles, each with amount 7 and a place, the looters carry 0 afterwards (the same as spike S5).
`recover_loot` of one pile adds exactly 7 Planks to the stock of the player region (read with `getStockOfGood`), the three together add 21, the ledger is empty, a second recovery of the same pile is refused.
The unit of `ItemsLooted` is still unknown (items or silver value). The ledger treats one unit as one item of the chosen good.

## What the real mod must do
Define its own pile (an actor, a building, or a table like this ledger), create it at the death place of a looter, and let peasants fetch it. Then `loot-drop-recovery` is adapted to read the pile of the mod (through `HarnessCommands`, see `mod-state-contract.md`).
`criteria.json` marks R3 as verified **on the stand-in** only, like the stand-in criteria of U10.
