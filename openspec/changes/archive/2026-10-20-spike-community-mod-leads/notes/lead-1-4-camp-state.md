# Lead 1.4: squad camp state

Probe: test scenario `probe-lead-camp`. Command `lead_squad_camp`.

## Result (run 20261021-043111-bea3)
- `Squad.camp`, `campLocation` and `rallyingStatus` could NOT be read. They are fields of the `Squad` struct. The only reader found (`SquadComponent:GetSquad`) ends the game (see `lead-1-2-stances.md`, run 20261021-041541-74de). So `lead_squad_camp` no longer reads the struct and returns only the squad ids (`HarnessLeads.READ_SQUAD_STRUCT = false`). The camp fields stay unknown. A bridge `get_property` on a struct copy was not tried (same risk).
- What the units show instead: a new AI lord at war, one army (32 units), no challenge, read through `lords_state` every 15 game seconds. The army was not still. It walked about 17500 game units north in the first 30 s, then stopped near (-30000, -22200) with its target equal to its position (waiting).
  - 15 s: (-31681, -40334), target (-31588, -39934), 32 alive
  - 30 s: (-31113, -22805), target (-30850, -22897), 32 alive
  - 45 s: (-29734, -22216), target (-29759, -22129), 30 alive
  - challenge started; 15 s later: (-30005, -22182), 25 alive; 30 s later: (-29709, -22161), target (-22273, -16475), 20 alive
- So a waiting army shows as "position close to target" and a marching army as "target far from position". The army also lost units while it waited (probably the player village militia).

## Risks
- Reading the `Squad` struct crashes the game. Do not retry without a new access path (for example a hook that gets the struct as an argument).

## Does a mod feature need it?
No. The invasion mod can use `lords_state` (position, target, alive) to see waiting and marching. Drop this lead.
