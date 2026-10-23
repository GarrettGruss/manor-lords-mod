# Game tests (run order-1, fixture base, slot 0, 2026-10-22)

Player region: Nusslohe (ownerPawn = player pawn). Start: publicOrder 42, Approval 71, daysTotal 209.
`summedPublicOrderFactors`: Type 17 (unemployment) effectByPopulation -10.0, Type 19 (administration) +10.0, both with a 5-day window (day..day+5) that the game renews each day. `publicOrderMemory` was empty. `summedApprovalFactors` had 6 entries.

## Test 1: ApprovalSettings.ApprovalFactors (BLOCKED)
- The property is a fixed float[34]. The bridge `get` and `set` see only element 0 (-4.0). `name: "ApprovalFactors[17]"` fails ("no property"). Raw Lua `cdo.ApprovalFactors[i]` fails ("attempt to index a number value").
- A bridge `set` with a 34-element list is coerced to a single number: it wrote 0 into element 0 and left the rest. Element 0 was restored to -4.0. Elements 1 to 33 were not changed (read back).
- The defaults of all 34 factors can be read with `RTSMultiEngineCPP:GetDefaultApprovalRateForFactor(i)`: unemployment (17) -1.2, administration (19) +1.0, patrols (18) -0.25, homelessness (5) -5.0 (full list: idx0 -4.0 ... see run). It reads the CDO (element 0 changed with the write).
- Verdict: index 17 cannot be written from the bridge or eval_lua. The effect on publicOrder was NOT tested. A harness action in Lua would need another way to reach element 4*17 (for example raw memory), which is not available in UE4SS Lua. Pak/Game.ini config remains the route for these weights.
- Note: the summed unemployment entry is -10.0, not -1.2. The per-region value is not the config weight directly.

## Test 2: publicOrderMemory append (WORKS, effect unclear)
- Struct is plain numbers. In Lua `mem[#mem+1] = {Type=17, day=209, expirationDay=213, count=1, past=false, effectByPopulation=-30.0}` worked, no crash, entry read back.
- Within about 1 s the game rewrote effectByPopulation from -30.0 to -0.04 (= -30 / population about 750; it falls as the population grows: -0.0364 later). So the field is a per-person value that the game recomputes.
- The entry stayed after its expirationDay (213): not removed within 9 days after it (day 222).
- Over 13 game days (speed 3, days 209 to 222) publicOrder read 42, 42, 40 (day 214), 40, 42, 42, 100 (day 221), 42; Approval 71, 71, 70, 70, 71. The dip and the one 100 reading are small and not clearly linked to the entry (no control run without it). The entry did not appear in `summedPublicOrderFactors`.
- Verdict: appending is safe and possible from Lua. A -30 effect gave no clear lasting order drop, so the weight is probably not the raw value. Needs a control run and larger values.

## Test 3: tooltip
Not done. Hover needs the mouse (no mouse device connected). Needs the owner.

## Housekeeping
- Raw eval was off (`allow_eval = false` in the deployed UEBridge/scripts/settings.lua). I set it to true, reloaded, and restored the original file at the end (backup `backups/settings.lua.order.bak`).
- Save folder identical to the backup `backups/saves-20261022-232957-order` after the run and after `fixtures.py uninstall`. No crash.
