## ADDED Requirements
<!-- Issue: #583 -->

### Requirement: The feature gives a read-only revolt status
The feature SHALL give the order tooltip a read-only status of the next revolt: `days` (days to the revolt, or to the next try after a blocked revolt) and `blocked` (a text or nil). The status SHALL be nil when no banditry timer runs. The status SHALL change no state, start no timer, make no Outlaws pawn and send no event. `blocked` SHALL be set when the number of valid armed families is below `leavers_for` (and `leavers_for` is above 0), or when the Outlaws pawn does not exist. The count of valid armed families SHALL be cached for `armed_cache_seconds` (default 3) real seconds.

#### Scenario: Days to the revolt
- **WHEN** the timer started 20 game days ago and `timer_days` is 60
- **THEN** the status has `days` 40
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: Days to the next try
- **WHEN** the timer expired, the revolt was blocked at the current tick count, and the last tick was 18 game days ago
- **THEN** the status has `days` 12 (`tick_days` is 30)
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: The status has no side effect
- **WHEN** the status is read with too few armed families and no Outlaws pawn
- **THEN** no pawn is made, no timer or order value changes and no family leaves
- Checked by `harness/tests/test_fakegame_bandits.py`.
