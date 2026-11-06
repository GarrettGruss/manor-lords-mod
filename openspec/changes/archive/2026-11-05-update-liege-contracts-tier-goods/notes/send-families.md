# Send families away (spike 1.2)

Run 20261106-001135-9e7b (slot 1, fixture `playtest-noai`, variant `families`). The fixture has 5 families (15 people).

- `ManorCore.remove_families(region, 3)` (the call of the bandits and the vassals: collect the members, then `just_die`) removed 3 families and 9 people. `workerFamilies` went from 5 to 2, `sack_census` from 5 families / 15 people to 2 / 6.
- The count stayed 2 for 3 more game days (no refill in that time). No crash.
- The first run of this spike (20261106-000745-78f3) sent a probe mode with an underscore in its name; the command bridge refused it ("unknown mode nil"). Modes of `loan_probe` must have no underscore.

Verdict: `send_families` uses `ManorCore.remove_families`. The mod keeps at least one family (config `min_families_left`). Not run together with `family_add` and `building_assign_worker` (DANGEROUS_ACTIONS.md).
