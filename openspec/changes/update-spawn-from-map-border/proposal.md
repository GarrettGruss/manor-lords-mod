# Proposal: update-spawn-from-map-border

Issue: #434

## Why

Owner requirement (2026-10-23): when the mod spawns units, they arrive from the map borders. They must not appear next to the target. Today every mod spawn puts the squads near the player pawn or the manor:

- a lord raid: `lords.lord_spawn_army` with `dx = 0, dy = start_dy` (-50000) from the player pawn;
- the great raid waves and the final army: the same call;
- the relief army: `relief_offset` (0, 2500) from the manor centre;
- the test spawns of HarnessBattle.

An army that pops up at the village is not "dread from knowing" (pillar 4). A raid that walks in from the edge is announced by its approach, and the player sees it come. It also matches the game's own raiders.

Design reference: `design/mod/invasion-mod.md`, pillar 4 (dread from knowing: raids are announced and seen) and pillar 5 (raids have goals). The change keeps all pillars. It changes where units appear, not how many, when, or why. No decision number applies yet.

## What changes

- New requirement `Spawned armies arrive from the map border` in `mod/invasion`. It covers every hostile or arriving army of the mod: role raids (lord raid), great raid waves, the final army, the relief army, and raid stand-ins.
- `mod/invasion` requirements that say where or when an army spawns are modified: `The raid spawns on the planned day`, `A role raid is the army of an AI lord`, `The great raid starts with waves`, `A relief army and a final battle end the great raid`.
- Method (after the spikes): spawn the squads of the AI lord at a border point 3000 units outside the map edge. The lord has a challenge at the manor, so the army walks in. The arrival time argument of `spawnArmy` does not work (spike A). The relief army cannot walk in (spike C).

## Which spawns

| Spawn | Code | Side |
|---|---|---|
| Lord raid squads | `invasion/lord_raid.lua` -> `HarnessLords.lord_spawn_army` | hostile |
| Great raid waves, final army | `invasion/init.lua` (`spawn_great_army`) -> lord raid | hostile |
| Relief army | `invasion/relief.lua`, `relief_offset` in `config.lua` | player |
| Raid stand-ins (no lord) | `HarnessBattle.spawn_at` | hostile |

Not in this list: squads that the player pays for (`manor_stronghold/squads.lua`, retinue). They are the player's own men and stay at the manor.

## Non-goals

- No change of raid size, raid day, composition or balance.
- No new map, model or animation.
- No change of the native game raids. They already arrive from the border.
- No change of squads that the player hires.
- No performance fix. Less load at the spawn instant is only a possible side benefit (see design).

## Decisions of the owner (2026-10-28)

1. Which border: the border point nearest to the target is sufficient. DECIDED. New wish: the game tells the player from which direction the raid comes (8 compass words). Built as the requirement `The game tells the player from which direction the raid comes`.
2. Arrival 1 to 3 game days (`arrival_days`): DECIDED, but the game call cannot do it. The arrival days argument of `spawnArmy` is ignored for a lord army (spike A). The army walks in from the border. The march takes 3 to 8 game days. The mod spawns `march_lead_days` (5) days before the raid day. See `notes/arrival-days.md` and `notes/map-border.md`.
3. The raid starts at arrival (the banner counts to the raid day, the raid tracker and the leave rules start at arrival): DECIDED and built.
4. (Closed 2026-10-24.) Bandits of a family conversion are not part of this change (change `update-banditry-bandit-camp`).
5. The relief army comes from the border nearest the manor, away from the enemy border point: DECIDED, but NOT POSSIBLE with the known calls. A player squad cannot be moved from Lua. A friendly AI lord army crashed the game twice (notes `march-order.md`). The relief army stays at `relief_offset` next to the manor until the owner decides. Options for the owner: accept the relief army at the manor; or give a spike more time (a vassal lord of the game, a squad order); or remove the relief army from the great raid.

Each question was answered by the spikes in `tasks.md`.
