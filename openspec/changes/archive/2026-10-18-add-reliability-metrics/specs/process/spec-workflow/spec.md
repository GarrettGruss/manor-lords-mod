## ADDED Requirements
<!-- Issue: #289 -->

### Requirement: A proposal states the reliability risk of its domains
The proposal of a `feat` change SHALL have a section `Reliability risk` with one line for each domain the change touches. Each line SHALL be copied from the latest assessment report (`docs/reliability/`) and SHALL show the change failure rate, the flaky rate and their sample counts.

#### Scenario: A feat change in two domains
- **WHEN** a `feat` change touches `mod/tribute` and `harness/run-launcher`
- **THEN** its proposal has a `Reliability risk` section with one line for each of the two domains, with sample counts
- Checked by review.
