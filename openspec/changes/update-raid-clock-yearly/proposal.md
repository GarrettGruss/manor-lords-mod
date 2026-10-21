# Proposal: Update raid clock yearly

Issue: #339.

## Why
Owner decision (2026-10-20, `decide-open-mod-rules`, answer 1): "One raid per year. No raids in the first year. A random chance per season decides when it comes."

Today the mod plans the first raid 30 to 90 game days after the start, and plans the next raid 60 to 120 game days after that. The raid pace is not tied to the game year.

## What Changes
- The mod plans no raid in the first game year.
- From the second game year, one raid comes in each game year.
- At each season change the mod rolls a random chance. The chance rises with each season of the year that passes without a raid, so the raid comes at the last season at the latest.
- The raid kind (plunder or subjugation) of a yearly raid follows the existing rules for the kind. Only the timing changes.
- The first-raid day range (`first_raid_days_min`, `first_raid_days_max`) and the subjugation wait range (`subjugation.wait_days_min`, `wait_days_max`) are removed.
- The warning banner keeps its rule, but a raid that comes by a season roll gets its warning time from the day of the roll.

## Non-goals
- The great raid clock (3 to 5 game years), its waves and the final battle.
- The raid size, the difficulty and the raid behavior.
- Bandit conversion rolls (`mod/bandits`); they keep their own season roll.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `mod/invasion`: new requirements "No raid comes in the first game year" and "One raid comes in each later game year, by a season roll". The requirement "The first minor raid is planned within a day range" is removed. "A subjugation raid follows the first raid" and "The raid spawns on the planned day" change.

## Impact
- Code: `mod/InvasionMod/Scripts/features/invasion/` (`plan.lua`, `init.lua`, `lord_raid.lua`), `config.lua`.
- Tests: `harness/tests/test_fakegame_invasion.py`; the test scenarios `first_raid.py`, `no_double_raid.py`, `subjugation_raid.py` and a new yearly raid test scenario.
- Wiki page for the invasion feature, `CHANGELOG.md`.
- Real game runs, one at a time.
