# Q3: sequence with the hide route

Run `corpses-5`, t 4851: `spawnBanditCamp` (creates Outlaws, 18 units), `addPawnRelations`, `remove_families(2)`, `SetActorHiddenInGame` on the 6 new bodies, `spawn_at bandit Brigands` at each home.

- Families 5 -> 3, people 6, bodies 6, all hidden (`bHidden` true for 6 of 6 until the actors vanished). Bandit units 18 -> 54. Picture: `evidence/q3-squads-at-homes.jpg`.
- Bodies left the list at about t 6050 and the actors were gone later. No crash.
- Raid and leave NOT confirmed: in `playtest-noai` the squads walked to (-25400,-55500), 14 000 units from the player, and stood there for 1 350 game s with no attack (one early rubble building, a burn at day 1). This agrees with the known no-AI result. A fixture with AI lords is needed to test the raid.
- A new family arrived about every 3 game days after the removal (immigration refills the village).
