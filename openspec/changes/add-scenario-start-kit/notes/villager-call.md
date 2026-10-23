# Villagers of a new game (task 1.2)

Real run 20261023-223641-7105 (new game, menu open): the player region has 5 families of 2 people = 10 people
(`getNumTotalPopulation` = 10, one homeless tent), and silver 0. So the game start already gives 10 people.

Decision: the kit makes the population exactly 10 (config `villagers`).
- More than 10 people (another Starting Supplies or population setting): the mod kills living members, last family first,
  with `member:just_die()` (same call as `ManorCore.remove_families`) until `getNumTotalPopulation` is 10.
- Fewer than 10 people: no safe call adds people. `settleRegion` crashed the game from Lua for the player pawn (see `ManorCore`),
  and `AddNewFamily` only splits a family. The mod logs a warning and keeps the people it has.
