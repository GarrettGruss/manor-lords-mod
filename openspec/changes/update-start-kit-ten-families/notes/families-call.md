# Adding families at Begin (task 1.1)

Real runs 20261028-235239-119a (slot 1) and 20261028-235402-4828 (slot 2), new game, pak InvasionMod:
- Before Begin: the player region has 5 families (10 people), as in the archived villager-call note.
- At Begin the mod calls `refugees.world.send_settlers` (ManorCore `settle_region`, player pawn, owned region): 1 call adds 5 families.
  Result: `getTotalNumFamilies` = 10, `getNumTotalPopulation` = 20. No crash.
- New families are homeless families in a tent camp (camp spot: woods, else near the village, else the settled centre). The game moves them into houses later.
- A call adds whole groups of 5, so the count can pass the target (8 families + 1 call = 13). The mod then removes the last families with `just_die` (tested in the fake game only; the real game never needed it).
- The people count depends on the family size (new families have 2 people). The test asserts the family count exactly and the people count only in a range.
- The save folder hash changed in `rtsSettings.sav` only (the owner played in slot 0 at the same time); no `saveGame_*` file changed.
