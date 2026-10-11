# Coverage after the manor worker slots (spec 12, Q7)

Date: 2026-10-11. Branch `feat/34-manor-storage-workers`. Tool: `harness/tools/coverage.py`.

- M1 (the manor can store goods) was extended: the manor storage building also needs a worker slot with the storehouse or granary role, and that worker must serve the store.
  It was set to not verified, then verified again with the scenario `manor-storage-workers`: 3 of 3 real runs (`manor-storage-workers-v2-1` to `-3`).
  The first real run (`manor-storage-workers-1`) failed the control: builders still brought 4 units to the site in the first 2 game days. The scenario now waits 2 game days first and counts all goods, not one.
- Base game: the slot data, the role and the assignment function. Mod-defined: the write of the Keep row in `buildingStats` (in memory). Harness shortcut: finishing the Keep.
- Not verified: carrying goods out of the Keep, a full castle with modules, a Keep that the game finished by itself.

Result: 36 of 39 A and P criteria with a verified method (92%, target 90%). Blocked: O1 to O4, R5, S4, S5 (unchanged).
