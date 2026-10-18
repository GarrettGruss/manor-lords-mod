# M02 iteration 07: notes

## Design
- The raid itself still walks to the manor. A raid cannot be steered to another region. So "target" is a rule of the mod, not a path.
- "Succeeds" (TBD): a subjugation raid on a vassal region, active 8 game days with at least half of its units. Then `lose_vassal(slot, "taken")`. Config `tribute.siege`.
- Only handed-over vassals that are not the fallback capital and have not submitted are targets.
- Losing a vassal only frees the slot (and sends refugees). The region owner is not moved (it crashes the game, M07.04 notes).
- The code lives in the `tribute` feature (`init.lua`), because it needs vassals and the raid tracker. `invasion` gets a provider hook, so it needs neither.

## Findings
- Real runs: the vassal fell 80 to 110 real seconds after the spawn (8 game days at speed 3).
- The first raid (plunder) still targets the home region, so its end changes no vassal loyalty.

## Risks seen in this iteration
- One run ended `harness_error`: `HarnessCommands.lua:278 bad argument #2 to 'write' (string expected, got table)` while the answer to `invasion_force_next` was written. `json.encode` returned a non-string. It did not repeat in 3 later runs. Cause not found.
- One run of the unchanged scenario `invasion-subjugation-raid` ended in a native crash during `SACK step people` (run `20261018-101743-0194`, no vassal lord in that run). It passed in the next run.

## Open
- The siege does not know what the player did. A better rule (player army in the region) is not designed.
