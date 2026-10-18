# Recommendation for M00 (spec 29)

Date: 2026-10-18.

## Hand cannons: bring them back, as a stand-in
- A new unit row works end to end through a pak: it loads, spawns by name from Lua and fights. A weapon item cloned from the crossbow with higher `rangedAtt` and `armorPierce` changes the fight strongly (A/B N=5, run ids in `part-a-ab-results.md`).
- The look stays a crossbow. A real gun mesh, projectile and effect do not exist as data. Use the name "handgunner" in the design but accept the crossbow model. The gun sounds and smoke assets in the game are not connected to units by data.
- The player cannot recruit it from the native screen. The screen has 5 fixed cards. For version 1 the mod spawns the unit (for example in the manor retinue flow or as AI army units). A widget pak with a new card, or repointing a card `unitType`, is the next spike if player recruiting is required.

## War wagons: keep them out of version 1
- No vehicle, siege or movable obstacle class exists that the AI and pathing respect. Spawned carts are meshes only: the path obstacle count does not change.
- The stand-in `warWagon` squad (small, high def and block, slow item) spawns and fights, but it has no wagon model, does not block and does not shelter archers.
- If wanted later: use the stand-in squad in an AI army, or build a real wall piece with the building system. Do not rely on spawned actors.

## Next steps, if the design needs more
1. Spike: widget pak with a sixth recruit card (spec 16 method) and a click test with the real recruit handler.
2. Spike: separate `Speed`, `shootingRange` and reload effects of the weapon item (one field at a time, A/B).
3. Spike: gun look with a pak (new item mesh name and sound), after the spec 21 mesh route.
