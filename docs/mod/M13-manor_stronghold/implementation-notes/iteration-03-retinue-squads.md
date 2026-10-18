# Iteration 03: retinue squads

- `spawnArmy(position, {FName("retinue_tier1")}, playerRef, 0, 0)` returns an array of squad handles (`.Value` is the id). It gives 36 men with side player (census role Soldier, squad type reads "?").
- `InitializeEmptyRetinueSquad(Region)` from the bridge fails: the region ref is passed as a string and the property needs a UObject. In Lua with a real object it is untested. An empty squad still needs a way to add men, which the native editor does; so the route is not useful.
- The limits 12 and 24 are code constants (LargerFormations patches the code). A data pak cannot change them.
- The mod route does not use the native retinue (no bound Retainer, no editor, no armour upgrade). It makes normal player squads with retinue equipment.
- Fight run: 36 of 36 men alive against 18 Brigands, bandits died (run 20261018-141824-1038).
- Open: save and load of the squads; real-mouse retinue editor was not needed.
