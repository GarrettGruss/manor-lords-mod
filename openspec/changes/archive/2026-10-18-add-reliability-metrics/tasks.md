# Tasks

## 1. Skill scaffold

- [x] 1.1 Find where a run records its test scenario path (`runner.py`, `config.json`); verify by review, write `notes/scenario-path.md`
- [x] 1.2 Create `.claude/skills/reliability-assessment/` with `SKILL.md` and `spec/README.md` (from the skill spec draft in `design.md`); verify by review
- [x] 1.3 Write `reliability.json` for this repo with all start values and a pattern for every capability; verify with a command that shows `unmapped` files under `thresholds.unmapped_churn`, output in `notes/unmapped-share.md`

## 2. Script

- [x] 2.1 Add the config loader and the domain map; verify with `uv run python -m unittest discover -s .claude/skills/reliability-assessment/tests`
- [x] 2.2 Add the git report (types, numstat, counts, ratio, churn, change failure rate); verify with tests on a temporary git repository
- [x] 2.3 Add bug lifetime with blame and `no_origin`; verify with tests on a temporary git repository
- [x] 2.4 Add the run report (timeline, flaky, MTTF, MTTR, skipped files); verify with tests on fake run folders
- [x] 2.5 Add `assess` (report files, domains over a limit, `low sample` marks); verify with a test
- [x] 2.6 Check that the script imports nothing from `harness/` and works with a config for another layout; verify with a test that uses a second config

## 3. First reports

- [x] 3.1 Run `assess` on this repository; verify by review, copy findings to `notes/first-report.md`
- [x] 3.2 Review the listed `fix` commits for label noise; record the decision in issue #289; verify by review

## 4. Process and docs

- [x] 4.1 Add the assessment step to the `harness-release` skill; verify by review
- [x] 4.2 Name the skill in `harness-overview` and `CLAUDE.md` skills list; verify by review
- [x] 4.3 Add a wiki page for the reliability assessment; verify with `wiki.py check`
- [x] 4.4 Add an `Added` entry to `CHANGELOG.md`; verify by review
