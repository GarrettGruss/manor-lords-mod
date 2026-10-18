## ADDED Requirements
<!-- Issue: #289 -->

### Requirement: The summary names the commit and the domain
`summary.json` SHALL hold the full commit SHA of the harness (`git_sha`) and a flag when the work tree was dirty, in addition to the short `git` value. It SHALL hold the domain of the test scenario (`domain`) from the domain map of `harness/reliability`. A test scenario that the map does not match SHALL have the domain `unmapped`. The summary SHALL stay under 4096 bytes.

#### Scenario: A run of a feature test scenario
- **WHEN** a run of `mod/InvasionMod/scenarios/tribute/<name>.py` ends
- **THEN** `summary.json` holds `domain` `mod/tribute` and a 40-character `git_sha`
- Not checked yet (planned: `harness/tests/test_runlib_summary.py`).
