## ADDED Requirements
<!-- Issue: #289 -->

### Requirement: A domain map assigns files and test scenarios to capabilities
The harness SHALL keep one domain map (`harness/reliability/domains.json`). It SHALL map path patterns to capability names (`harness/<name>`, `mod/<feature>`, `process/<name>`). A file under `mod/InvasionMod/Scripts/features/<f>/` or `mod/InvasionMod/scenarios/<f>/` SHALL map to `mod/<f>` without an entry. A path that matches no pattern SHALL map to `unmapped`. The tool SHALL fail with a clear message when a pattern names a capability that has no folder in `openspec/specs/`.

#### Scenario: A feature file maps without an entry
- **WHEN** the map is asked for `mod/InvasionMod/Scripts/features/tribute/rules.lua`
- **THEN** the domain is `mod/tribute`
- Not checked yet (planned: `harness/tests/test_reliability_domains.py`).

#### Scenario: An unknown path
- **WHEN** the map is asked for a path that no pattern matches
- **THEN** the domain is `unmapped`
- Not checked yet (planned: `harness/tests/test_reliability_domains.py`).

#### Scenario: A pattern names a missing capability
- **WHEN** a pattern in the map names `harness/does-not-exist`
- **THEN** the tool exits with an error that names the pattern and the capability
- Not checked yet (planned: `harness/tests/test_reliability_domains.py`).

### Requirement: The git report gives change metrics per domain
`reliability.py git` SHALL read the commit history of the current branch and sort each commit by its Conventional Commits type. Merge commits SHALL be skipped. For each domain it SHALL report: the `feat` count, the `fix` count, the fix-to-feat ratio, churn (lines added plus removed), and the change failure rate. A commit that touches several domains SHALL count once in each of them. The report SHALL show the share of `unmapped` churn.

#### Scenario: A commit in two domains
- **WHEN** one `feat` commit changes files in `harness/run-launcher` and `mod/tribute`
- **THEN** each of the two domains counts 1 feat
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).

### Requirement: The change failure rate uses a time window
The change failure rate of a domain SHALL be the share of its `feat` commits that are followed by a `fix` commit in the same domain within N days. N is the option `--window-days`, default 14.

#### Scenario: A fix inside the window
- **WHEN** the report runs on a test repository with 3 `feat` and 1 `fix` commit in one domain, the fix 5 days after the second feat
- **THEN** the domain shows 3 feat, 1 fix, a ratio of 0.33, and a change failure rate of 0.33
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).

#### Scenario: A fix outside the window
- **WHEN** a `fix` comes 20 days after the only `feat` and the window is 14 days
- **THEN** the change failure rate of the domain is 0
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).

### Requirement: The git report estimates bug lifetime
For each `fix` commit, the report SHALL find the commits that last changed the lines that the fix removes or changes (`git blame` on the parent commit). The bug lifetime SHALL be the time from the newest of those commits to the fix. A fix that only adds lines SHALL have no lifetime and SHALL be counted as `no_origin`. The report SHALL give the median lifetime and the sample count per domain.

#### Scenario: A fix changes a line from an earlier feat
- **WHEN** a `fix` changes a line that a `feat` commit wrote 3 days earlier
- **THEN** the lifetime of that fix is between 2.9 and 3.1 days
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).

#### Scenario: A fix only adds lines
- **WHEN** a `fix` adds lines and changes none
- **THEN** it counts in `no_origin` and not in the lifetime median
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).

### Requirement: The run report gives failure and repair times per test scenario
`reliability.py runs` SHALL read every `runs/*/summary.json` and order the runs by `started`. It SHALL group them by test scenario and by domain. The verdicts `fail` and `crash` SHALL count as a failure. Other verdicts except `pass` SHALL be counted apart. For each group the report SHALL give: run count, failure count, flaky count, MTTF (median time from a pass to the next real failure) and MTTR (median time from a real failure to the next pass). An unreadable summary SHALL be listed and skipped.

#### Scenario: A failure and a repair
- **WHEN** a test scenario passes at hour 0, fails at hour 10 on commit A, and passes at hour 14 on commit B
- **THEN** the report shows one failure, MTTF between 9.9 and 10.1 hours, MTTR between 3.9 and 4.1 hours, and 0 flaky
- Not checked yet (planned: `harness/tests/test_reliability_runs.py`).

#### Scenario: A broken summary
- **WHEN** one `summary.json` is not valid JSON
- **THEN** the report lists its path as skipped and still reports the other runs
- Not checked yet (planned: `harness/tests/test_reliability_runs.py`).

### Requirement: The run report separates flaky failures
A failure SHALL be flaky when the next run of the same test scenario on the same commit passes. Flaky failures SHALL be counted per test scenario and domain, and SHALL not count in MTTF or MTTR.

#### Scenario: A flaky failure
- **WHEN** a test scenario fails and the next run on the same commit passes
- **THEN** the failure counts as flaky and not in MTTF or MTTR
- Not checked yet (planned: `harness/tests/test_reliability_runs.py`).

### Requirement: Reports show sample sizes and are machine-readable
Both reports SHALL write a JSON file and print a Markdown table. Each ratio, rate and median SHALL appear with its sample count. A value with fewer than 3 samples SHALL be marked as `low sample`.

#### Scenario: A domain with two fixes
- **WHEN** a domain has 2 fixes with a lifetime
- **THEN** the median lifetime is shown with `n=2` and marked `low sample`
- Not checked yet (planned: `harness/tests/test_reliability_git.py`).
