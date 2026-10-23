# Evidence

Test scenario `raid-behavior-pit-loot`, run `20261023-032125-a80d` (pass; the alert "Storage is full" in pit_after.jpg is fixed, see notes/corpse-pit-capacity.md). Compressed to 1280x720 at most.

| File | Moment |
|---|---|
| pit_before.jpg | Hussite raid plundered (record: 18 of good 15); pit empty, before the raiders are killed. |
| pit_after.jpg | After a body reached the pit: pit holds 1 body (Type 233) and 1 share of good 15. |
| pit_full_alert_before_fix.jpg | Probe run `20261023-162615-aa18`, before the fix: 1 unit of good 15 added to the pit shows "Storage is full (Corpse Pit)". All storage limits of the pit are 0. |
| pit_after_limit_raised.jpg | Test scenario `raid-behavior-pit-loot`, run `20261023-162856-41a4` (pass), after the fix: the pit holds the share and the alert is gone. The picture does not show the pit inventory (no pit panel was open); the inventory is asserted in the test scenario. |
