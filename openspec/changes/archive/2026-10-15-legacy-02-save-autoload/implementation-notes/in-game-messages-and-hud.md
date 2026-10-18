# In-game messages and HUD values

Date: 2026-10-09. Source: a screenshot from the user, and read-only bridge calls in the running game (loaded `saveGame_0`).

## The "A New Message" banner
- The user explained it: the in-game notification is the way the player talks to the AI players (letters between lords).
- The banner is part of normal play. It is not an error, and it is not a harness problem.
- It shows up when a letter arrives. After a load, a welcome letter can arrive.
- Data: `PawnCPP.InBox` is an array of `Letter` structs. The first entry has `daySent` 6 and `paras` `["welcome_from_hildebolt"]`.
  `Letter` also has a `Guid`. The jmap lists `InBox`, `outbox` and `log` on `PawnCPP`.
- AI lords are also `PawnCPP` objects. The harness could read the `InBox` and `outbox` to test features that use letters.

Open:
- Does the banner block game input or the pause? It was visible while the game was running. Not tested.
- Does it matter for screenshots? It covers the middle of the screen for a while. The harness should note that in a screenshot.

## HUD numbers matched to properties
The HUD shows the region "Hochweg". The values read from the game match the screen:

| HUD (screenshot) | Property | Value read |
|---|---|---|
| thumbs up 50% | `Region.Approval` | 50 |
| scales 90% | `Region.publicOrder` | 90 |
| coins 50 (right of the scales) | `Region.regionalWealth` | 50 |
| barrel 2 (red) | `Region.supplies_food` | 2 |
| house -5 (red) | `Region:getNumHomelessFamilies()` | 5 |
| coin stacks 0, 0, 0, 0 (top right) | `PawnCPP.silver`, `influence`, `kingsFavour` | 0, 0, 0 |

Also read: `Region:getNumTotalPopulation()` = 10, `settlementLevel` = 0, `isSettled` = true.
The mapping of the icons to properties is my reading of the screenshot. The values are the same, but this is not proof that the HUD uses these exact properties.

## What this means for telemetry
- These properties are good first telemetry for a region: `Approval`, `publicOrder`, `regionalWealth`, `supplies_food`, population, homeless families.
- The player values `silver`, `influence` and `kingsFavour` are 0 at the start, as the user said.
- The screenshot is of the game window (window controls at the top right). The harness can capture it.
