# Proposal: Add vassal sack wipe

Issue: #341.

## Why
Owner decisions (chat, 2026-10-20), in `openspec/changes/decide-open-mod-rules/design.md`, items 4, 5, 10 and 11:

- Item 4: "Capital moves are not part of the game. No terms after a sack of the player. A Hussite sack of a vassal is complete when 80 percent of its buildings are ruins: all its villagers are deleted, and a homeless wave of 50 percent of its population starts. Test what happens to an AI village when all its villagers are killed."
- Item 5: "See 4. Loss by `take_by_lord` is dropped (it crashes the game)."
- Item 11: "See 4. The land of a lost vassal stays a village of rubble. The player can spend gold to raise its villager count to 5; then the AI rebuilds the village and its tribute starts again."
- Item 10: "For now the mod controls only the sacking of houses in an AI village. Any other effect on a region the player does not control goes through the review cycle (its own change)."

Today a lost vassal only frees its slot and the lord keeps the land. The fallback capital move takes a vassal region back, and the loss mode `take_by_lord` crashed the game.

## What Changes
- Remove the fallback capital move (`fallback_*` commands and requirement).
- A sack of the player region offers no terms after it.
- A Hussite sack of a vassal runs through the mod sack of houses. The sack is complete when 80 percent of the buildings of the vassal region are ruins.
- At that point the mod deletes all villagers of the region and the vassal is lost. A homeless wave of 50 percent of the population before the wipe starts (refugees).
- The land stays a village of rubble. The player can pay gold to raise its villager count to 5. Then the AI rebuilds the village and the tribute of the vassal starts again.
- Drop the loss mode `take_by_lord` and the command `vassals_set_loss_region`.
- The tasks start with a spike: what an AI village does when all villagers are dead, and whether a count of 5 makes the AI rebuild.

## Non-goals
- Vassal loyalty. The change `remove-vassal-loyalty` (#344) removes it.
- Any effect on an AI region other than the sack of houses (owner, item 10). The mod does not give orders to the AI rebuild; it only adds villagers.
- Changes to the raid clock, the sack of the player region and the fatal sack rule.
- Game design text in `design/mod/`.

## Design pillars
Serves the decision that a lost battle sacks the town and does not end the game. Keeps pillar 2 (rule through others) and pillar 3 (scarcity forces expansion): a wiped vassal stops its supply until the player pays to restore it. It does not contradict a pillar.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/vassals`: "A lost vassal frees its slot" changes (wipe, no `take_by_lord`). New: "A Hussite sack wipes a vassal at 80 percent ruins" and "The player can restore a wiped vassal".
- `mod/sack_and_terms`: REMOVED "A fortified vassal becomes the fallback capital". "The sack hits the right region" and "The feature offers named commands" lose the capital parts. New: "No terms after a sack of the player".
- `mod/refugees`: "A lost vassal sends a refugee wave" uses 50 percent of the population.
- `mod/tribute`: "A long siege takes a vassal" starts the sack of houses.

## Impact
- Code: `mod/InvasionMod/Scripts/features/vassals/`, `sack_and_terms/` (fallback files), `refugees/`, `tribute/`, `config.lua`.
- Tests: `test_fakegame_vassals.py`, `test_fakegame_fallback.py` (removed), `test_fakegame_sack_and_terms.py`, `test_fakegame_refugees.py`, `test_fakegame_tribute.py`; test scenarios `fallback_capital.py` (removed), `sack_region.py`, `loss_and_submission.py`, `refugee_wave.py`.
- Overlap: `remove-vassal-loyalty` (#344) also changes the requirement "The feature offers named commands" of `mod/vassals`. Merge one first and rebase the other.
- Real game runs, one at a time.
