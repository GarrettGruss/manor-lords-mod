# process/reliability-assessment Specification

## Purpose
TBD - created by archiving change add-reliability-metrics. Update Purpose after archive.

## Requirements

### Requirement: Reliability is assessed at fixed points
The reliability assessment (skill `reliability-assessment`, sub-command `assess`) SHALL run before each release, when the spec pull request of a `feat` change is opened, and once each month. Each run SHALL write its report to `docs/reliability/YYYY-MM-DD.md` with the JSON beside it.

#### Scenario: A release
- **WHEN** a mod release is prepared with the skill `harness-release`
- **THEN** an assessment report of that day exists in `docs/reliability/`
- Checked by review.

### Requirement: A domain over a limit gets a hardening change next
When the assessment marks a domain over a limit (`thresholds.cfr` or `thresholds.flaky` in `reliability.json`, with at least `thresholds.min_samples` samples), the next change in that domain SHALL be a regression test scenario or a change that only fixes defects. A `feat` change in that domain SHALL say in its proposal why it goes first, if it does.

#### Scenario: A domain over the change failure limit
- **WHEN** the report marks `mod/raid_behavior` over `thresholds.cfr`
- **THEN** the next change in `mod/raid_behavior` adds a regression test scenario, or its proposal says why not
- Checked by review.

### Requirement: The domain map is kept current
When the `unmapped` churn share in a report is above `thresholds.unmapped_churn`, the domain map in `reliability.json` SHALL be updated before the next assessment.

#### Scenario: Many unmapped files
- **WHEN** a report shows an `unmapped` churn share above `thresholds.unmapped_churn`
- **THEN** a commit adds patterns to `domains` before the next report
- Checked by review.

### Requirement: Noisy commit labels lead to issue-based tracking
When a review of the listed `fix` commits finds that the labels do not match real defects often enough to trust the counts, a change SHALL be proposed to track defects with GitHub issues.

#### Scenario: Mislabeled fixes
- **WHEN** the review of a report finds that many `fix` commits are not defect repairs
- **THEN** the finding is recorded in the change issue and a change for defect issues is proposed
- Checked by review.
