# Tasks

## 1. Test scenario

- [ ] 1.1 Find where `pause_calls` comes from (`harness/runlib/phases.py`); verify by review, write `notes/pause-calls-source.md`
- [ ] 1.2 Add `harness/scenarios/boot_timing.py` (history order, boot seconds, pause calls, 30 s clock check); verify with a fake game test in `harness/tests/` that runs it against a fake run folder
- [ ] 1.3 Run `boot-timing` once in the real game; verify that it passes, run id in `notes/real-runs.md`

## 2. Suite and domain map

- [ ] 2.1 Add `harness/suites/boot-timing.json` (repeat 5, no flake retries); verify with `uv run python harness/suite.py --suite boot-timing` in the real game, at least 4 of 5 pass, results in `notes/real-runs.md`
- [ ] 2.2 Map `harness/scenarios/boot_timing.py` to `harness/game-boot` in `reliability.json`; verify with `reliability.py runs`, the domain shows the new runs

## 3. Docs

- [ ] 3.1 Add the scenario to the `harness-run-scenario` skill list if it lists scenarios; verify by review
- [ ] 3.2 Add an `Added` entry to `CHANGELOG.md`; verify by review
- [ ] 3.3 Run the full fake tests; verify `uv run python -m unittest discover -s harness/tests -p "test_*.py"` passes
