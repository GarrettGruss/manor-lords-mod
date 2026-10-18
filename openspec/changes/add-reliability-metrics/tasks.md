# Tasks

## 1. Domain map

- [ ] 1.1 Find where a run records its test scenario path (`runner.py`, `config.json`); verify by review, write `notes/scenario-path.md`
- [ ] 1.2 Add `harness/reliabilitylib/domains.py` and `harness/reliability/domains.json` with patterns for every `harness/*` capability; verify with `uv run python -m unittest harness.tests.test_reliability_domains`
- [ ] 1.3 Run the map over all files in `git ls-files` and keep `unmapped` under 15% of the files; verify with a command output in `notes/unmapped-share.md`

## 2. Git report (phase 1)

- [ ] 2.1 Add `gitlog.py`: parse commits, type, numstat, domains; verify with `test_reliability_git.py` on a temporary repository
- [ ] 2.2 Add counts, ratio, churn and change failure rate; verify with `test_reliability_git.py`
- [ ] 2.3 Add `blame.py` for bug lifetime and `no_origin`; verify with `test_reliability_git.py`
- [ ] 2.4 Add `report.py` (JSON, Markdown, `low sample` marks) and the `git` sub-command of `harness/tools/reliability.py`; verify with a test and one run on this repository, results in `notes/first-git-report.md`

## 3. Run report (phase 2)

- [ ] 3.1 Add `git_sha` and `domain` to `summary.json` in `harness/runlib/summary.py`; verify with `test_runlib_summary.py` (size stays under 4096 bytes)
- [ ] 3.2 Add `runs.py`: timeline, flaky detection, MTTF, MTTR, skipped files; verify with `test_reliability_runs.py` on fake run folders
- [ ] 3.3 Add the `runs` sub-command; verify with one run on the real `runs/` folder, results in `notes/first-run-report.md`

## 4. Docs

- [ ] 4.1 Add a wiki page for the reliability reports; verify with `wiki.py check`
- [ ] 4.2 Name the tool in the `harness-overview` skill; verify by review
- [ ] 4.3 Add an `Added` entry to `CHANGELOG.md`; verify by review
- [ ] 4.4 Decide from `notes/first-git-report.md` if `fix` labels are too noisy and solution 2 is needed; record the decision in the issue; verify by review
