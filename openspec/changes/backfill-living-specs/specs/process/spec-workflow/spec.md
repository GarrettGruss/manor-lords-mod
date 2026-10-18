# Spec Delta

## MODIFIED Requirements

### Requirement: Capabilities use three groups
A capability path SHALL start with `harness/`, `mod/` or `process/`. A `mod/<feature>` path SHALL use the feature folder name from `mod/InvasionMod/Scripts/features/<feature>/`, or `mod/core` for the shared parts of the Invasion Mod. Player behavior SHALL be specified only as part of the Invasion Mod; the earlier standalone test mods have no capability.

#### Scenario: A new mod feature capability
- **WHEN** a change adds the first requirement for the Invasion Mod feature `invasion`
- **THEN** its delta spec path is `specs/mod/invasion/spec.md`
- Checked by review.

#### Scenario: The shared parts of the Invasion Mod
- **WHEN** a change adds requirements for the feature loader or the scheduler
- **THEN** its delta spec path is `specs/mod/core/spec.md`
- Checked by review.

#### Scenario: A path outside the groups
- **WHEN** a change uses a capability path such as `specs/raids/spec.md` or `specs/mods/policy-menu/spec.md`
- **THEN** the review rejects the change until the path starts with `harness/`, `mod/` or `process/`
- Checked by review.

### Requirement: Spec scenarios name their test scenario
Each spec scenario for harness or mod behavior SHALL name the check that covers it, as "Checked by `<path>`": a test scenario, or a Python test file in `harness/tests/` for behavior that runs without the game. A spec scenario for a process rule SHALL say "Checked by review" or name the command that checks it. A spec scenario with no check yet SHALL say "Not checked yet". A THEN step for game behavior SHALL state a range, not an exact value.

#### Scenario: A mod spec scenario
- **WHEN** a delta spec adds a requirement for raid timing
- **THEN** each of its spec scenarios has a line such as "Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`"
- **AND** its THEN steps state ranges such as "between day 30 and day 90"
- Checked by review.

#### Scenario: A harness spec scenario checked without the game
- **WHEN** a delta spec adds a requirement for the run launcher
- **THEN** its spec scenario may name a Python test, such as "Checked by `harness/tests/test_runlib_summary.py`"
- Checked by review.

#### Scenario: Behavior without a check
- **WHEN** a requirement describes built behavior that no test scenario or Python test covers
- **THEN** its spec scenario says "Not checked yet"
- Checked by review.
