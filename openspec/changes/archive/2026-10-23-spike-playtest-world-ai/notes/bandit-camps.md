# Question 1: bandit camps with camp settings 0

Runs: `noai-q1b` (first game, one crash, see below), `noai-h-175358` (hold run, game driven through the bridge and named commands, slot 1).
Fixture `playtest-noai`: Initial bandit camps 0, spawn limit 0, Raider frequency None, AI opponents 0.

## Verdict

**The mod can make the bandit pawn and a bandit camp itself.** The game call `RTSMultiEngineCPP:spawnBanditCamp()` (no arguments) works with the camp settings at 0.

## Numbers

| Step | Before | After |
|---|---|---|
| `FindAllOf("PawnCPP")` in the fixture | 1 (the player). No pawn with `isBandit`. | |
| `bandit_state` (command) | refused: "no bandit pawn (isBandit) found" | |
| `HarnessBattle.spawn_at("bandit", ...)` | would return "no pawn for side bandit" (code `HarnessBattle.lua:173`, the owner's playtest error) | |
| one call `spawnBanditCamp()` | pawns 1, bandit pawns 0, units 201 | pawns 2, bandit pawn 1 ("Outlaws", trait `bandit`), units 219 (+18 Brigands) |
| `encampment_sites` (type 100) after the call | 0 sites | 1 site, 17 parts, `constructed`, owner = the new bandit pawn |
| second call | | a second camp (another place), +18 units, still 1 bandit pawn |
| `spawn_units side=bandit Brigands` (`HarnessBattle`) after the call | | works: 1 squad, 18 units, owned by the bandit pawn |
| `bandit_kill_squads` on all bandit squads | | the pawn stays (pawns count unchanged), a new bandit squad can be spawned |

Second fresh game (hold run): the same result (pawns 2 to 3 with the Probe Baron, bandit pawns 0 to 1, camp at region Krumme Leite, picture `evidence/q1-camp-spawned.jpg`).

## Details that matter

- The camp setting "Random bandit camp spawn limit 0" does not stop a direct `spawnBanditCamp()` call. Two calls made two camps.
- The new bandit pawn has **no relation row with the player** (`bandit_state.relation.missing = true`). `lord_relations` (`RTSMultiEngineCPP:addPawnRelations(pawn)`) adds it (relations 0 to 1, tags empty). Without the row, features that read relation tags of the bandit pawn need this call first.
- The bandit pawn has `enemies` = the player (hostile by default). Its squads walk: the camp squad stays, a second squad appeared by itself, walked to the player village ("Can raid = 0", the AI log says "enough looted. Leaving map"), and left. So a camp is not passive. In the hold run the player was not harmed in the 25 game days watched (families 5 to 7, no losses seen). Not measured in detail.
- The camp comes with 18 Brigands. A mod that only needs the bandit pawn (to own squads) gets a camp and 18 units as a side effect. Killing the units with `just_die` keeps the pawn. The camp buildings stay.
- `spawnNewAILord` is not needed. Setting `isBandit = true` on another lord pawn was not tried (no need).
- Other bandit functions found on the engine class: `spawnRaiders(NumSquads, ArmyCenter)`, `spawnEliteRaiders(ArmyCenter)`.

## Crash

Run `noai-q1b` crashed (UE crash report in the real `Crashes` folder, `EXCEPTION_ACCESS_VIOLATION reading address 0x328`, base dir `slots/2`) about 30 s after the first unpause at speed 3. At that moment the game had 3 bandit camps (3 calls), a second lord with `build=1`, a region taken with `lord_take_region`, and I had killed the camp squads with `just_die`. Two repeats did not crash: one camp, one lord with a founded village, 25 game days at speed 3; then killing all bandit squads and 12 more game days. The cause is not isolated. Treat "many camps at once" and "kill camp squads, then unpause" as unproven-safe.

## Recommendation (for the owner)

- The mod does not need the game setting "Initial bandit camps" for its own bandit features. When `pawnOf("bandit")` finds no pawn, the mod can call `spawnBanditCamp()` once, then `addPawnRelations` for the new pawn. It then gets the camp and 18 Brigands. This is a decision for the owner (open question: does the player want a camp in a world with camps at 0?). The cheaper option is the game setting Initial bandit camps 1.
- If the mod only needs a pawn without a camp, there is no tested route. A follow-up spike could try `spawnNewAILord` and set `isBandit`, or delete the camp actors.

## Not verified

- Whether a save and load keeps the bandit pawn made this way (no save was made).
- `spawnRaiders` without a bandit pawn (the pawn exists after the camp call).
- Camp behaviour over a full game year.
