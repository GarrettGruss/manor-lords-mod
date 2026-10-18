# Tasks

## 1. OpenSpec setup

- [x] 1.1 Run `openspec init --tools claude` and verify that `openspec/`, `.claude/skills/openspec-*/` and `.claude/commands/opsx/` exist
- [x] 1.2 Write `openspec/config.yaml` (context, rules, operations) and verify that `openspec instructions proposal --change adopt-openspec --json` shows the context and rules
- [x] 1.3 Check that an extra `feedback.md` next to a spec does not break the CLI (D8): make a temporary spec folder with it, run `openspec validate --all`, then delete the folder

## 2. Project rules

- [x] 2.1 Update CLAUDE.md sections "Specs and notes", "Git", "GitHub issues" and "Architecture" to the OpenSpec rules; verify by review against `specs/process/spec-workflow/spec.md`
- [x] 2.2 Add `docs/harness/README.md` (legacy, read-only) and update `docs/mod/README.md` to point new work to `openspec/`; verify both links resolve

## 3. Skills and wiki

- [x] 3.1 Update the skills `harness-overview`, `harness-git-workflow`, `harness-game-spike`, `harness-dispatch-agents`, `harness-coverage` and `repo-wiki` to the new paths and names; verify with a grep that no skill tells an agent to write new notes into `docs/harness/` or `docs/mod/`
- [x] 3.2 Update `docs/wiki/operations/docs-and-specs.md` (and the wiki log) to describe OpenSpec, the install, the telemetry opt-out and the legacy folders; verify with the repo-wiki check script

## 4. Changelog and checks

- [x] 4.1 Add the change to `CHANGELOG.md` under Unreleased (Added, Changed); verify by review
- [x] 4.2 Run `openspec validate adopt-openspec --strict` and the Python tests (`uv run python -m unittest discover -s harness/tests`); verify the validation passes and the tests give the same result as `main` (in WSL on 2026-10-18 both had 1874 tests, 5 failures and 155 errors in fake-game and slot tests that this change does not touch)

## Workflow follow-up

- Commit on `feat/adopt-openspec`, push, and open the pull request that closes #251.
- After the full tests pass, run `openspec archive adopt-openspec --yes` as the last commit, then merge.
