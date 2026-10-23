# Corpse pit capacity (PR #410 review)

Owner comment: "Storage is full on the corpse pit indicates some loot might be failing to populate."

## Result

Loot was NOT lost. The "Storage is full (Corpse Pit)" alert is only an alert.

- Probe run `20261023-162615-aa18` (fixture `base-corpse-pit`): `addToInventory` of good 15 on the pit, requested vs stored: 1->1, 10->10, 40->40, 100->100, 400->400, 2000->2000 (total 2551). `addToInventory` returned no error each time.
- The pit has `storageLimitGeneric`, `storageLimitLarge` and `storageLimitPantry` all 0 (also `numStored*` 0). Any good in the pit shows the alert, also 1 unit (picture `evidence/pit_full_alert_before_fix.jpg`).
- Probe run `20261023-162720-705b`: writing the three limits to 5000 from Lua works (read back 5000). The alert is gone after one game day.

## Fix

`world.pit_add` raises the three limits to at least the stored total after the add, before `addToInventory` (`world.pit_raise_limits`). The test state `raid_behavior_pit_state` shows `limit` for each pit. If a limit write fails, the add still keeps the goods (alert only).

## Checks

- Test scenario `raid-behavior-pit-loot`, run `20261023-162856-41a4` (pass): the gain equals the paid shares exactly (was `>=`), and the pit limit is not below the stored goods. Picture `evidence/pit_after_limit_raised.jpg`: no alert.
- Fake game test `test_a_pit_add_raises_the_storage_limits_to_the_stored_total`.
- Not verified: the limits are in the save of the building, so a loaded save keeps them; a pit built after a load starts at 0 and is raised on its first add. The alert for the corpses (type 233) alone is not tested.
