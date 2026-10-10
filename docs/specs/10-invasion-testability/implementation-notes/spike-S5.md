# Spike S5: loot drop

Date: 2026-10-10. Runs: probe-s5-a, series of `raid-loot` (3 of 3).

## Question
Can a unit that carries goods be killed, and can the dropped goods be found?

## Method
Commands `set_unit_loot` (write `SMUnit.ItemsLooted`) and `kill_units` (`SMUnit:just_die`) with `with_loot=1` and `actors=1`. The kill command reads the carrier state before the death and compares the number of actors by class before and after (`FindAllOf("Actor")`).

## Results
- `ItemsLooted = 7` written on 3 bandit units: read back 7 each, census loot total 21, max 7.
- `just_die` on those 3 units (found with `ItemsLooted > 0`): killed 3. The victims were at (-36727,-37259), (-37044,-36766), (-36971,-36262). Their `Inventory` had 0 entries before the death.
- After the kill (5 game seconds later): dead flag on 3 units, `ItemsLooted` total 0 (the game clears it on death), unit count unchanged (215, dead units stay in the list). A second kill of 2 units without loot: dead 5.
- No new actor class and no change in any actor count (`actor_changes` empty) at either kill. No ground goods object was found.
- Not checked: stock of a region or building near the death, `Inventory` of other units, whether the game gives the value back to an owner (the units were in a bandit camp region, Riesenbuckel, far from the player).

## Verdict
partial. Verified: kill units (`ctx.actions.kill_units`), write and read loot per unit (`set_unit_loot`, R2). Not verified: that loot drops on the ground or can be recovered (R3). Next step: kill a looter next to a settlement building and read the stock of that building and the region.
