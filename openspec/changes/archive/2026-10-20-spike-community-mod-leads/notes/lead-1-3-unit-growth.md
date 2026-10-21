# Lead 1.3: unit growth

Probe: test scenario `probe-lead-growth`. Command `lead_spawn_unit` (`RTSMultiEngineCPP:spawnCompleteUnit(FName(template), at, rotation, lordPawn, company, 0)`).

## Result (run 20261021-042957-de11)
- Works. A new AI lord had 1 army squad of 32 `spearMilitia` (challenge started, army marching). Three calls with the template `spearMilitia` (arrival 0 days) gave: squads 1 to 4 and units 32 to 128 (`spawn_calls_ok` 3, `new_squads_seen` 3). `lords_state` lists the new squads under the lord, so the lord commands them.
- The call returns a `Squad` struct. Do not read it (the `squadID` read gave a table, not a number). Find the new squad ids by comparing `lords_state` before and after.
- The new squads appear at the place given (player pawn plus offset). Whether the lord AI joins them to the march was not measured.
- `steer_state` gives 0 units for an AI lord squad (seen in run 20261021-042003-6464), while `lords_state` gives the right count. Use `lords_state` for lord armies.

## Risks
- Place: in the probe the units appear next to the player. A feature must choose the place (for example the army centre).
- A new squad is a full squad (32). A smaller growth step needs a template with a smaller `maxSize`.

## Does a mod feature need it?
Yes, for any feature that adds troops to a lord army during a challenge (reinforcements). It is the simplest lever found so far. Keep the command.
