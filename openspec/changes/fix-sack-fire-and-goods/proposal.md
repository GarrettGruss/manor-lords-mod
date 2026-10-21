# Proposal: Fix sack fire and goods

Issue: #325.

## Why
Run 20261020-112444-595a (test scenario `sack-ruins`) showed that sack fires go out within seconds, so burned buildings do not become rubble. The cause: villagers perform firefighting. The test set the fires with no enemy soldiers in the village. When enemy soldiers are in the village, villagers flee and do not fight fires (owner, 2026-10-20).

Owner decision (2026-10-21, `notes/decisions.md`): accept the loss. A burned store may lose goods in the fire. The mod itself removes no goods in a sack. Only the plunder mechanic removes goods on purpose.

## What Changes
- The sack no longer takes a share of the stock.
- The mod removes no goods from a sacked building. Fire may destroy part of them (accepted).
- Sacked buildings become rubble. The sack runs while the raiders are still in the village, so fires are not put out.
- The test scenarios `sack-ruins` and `sack` run the sack during a raid and check rubble and that the mod takes no goods.

## Non-goals
- The plunder tick (`mod/raid_behavior`). It stays the only way goods leave the village.
- Terms, tribute and the fatal sack rule.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/sack_and_terms`: "Sack size grows with difficulty" drops the stock share. New requirements: "The mod destroys no goods in a sack" and "Sacked buildings become rubble".

## Impact
- Code: `mod/InvasionMod/Scripts/features/sack_and_terms/` (`world.lua`, `init.lua`), `config.lua` (`sack.method`, a time limit).
- Tests: `harness/tests/test_fakegame_sack_and_terms.py`, the test scenarios `sack_ruins.py` and `sack.py`.
- Real game runs, one at a time.
