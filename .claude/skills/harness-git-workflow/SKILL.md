---
name: harness-git-workflow
description: Branch, commit, push, open and merge pull requests for this repo, and handle changelog and merge conflicts. Use whenever you finish a piece of work in the manor-lords-mod repo.
---

# Git workflow for this repo

Rules are in CLAUDE.md: atomic Conventional commits, one feature branch per spec, CHANGELOG kept current. Do not commit, push or merge unless the user asked or a standing goal grants it (for example the user's goal that allows merging pull requests).

## Branch and commit
- Branch from an up-to-date `main`: `git checkout -b feat/<NN>-<name>` (or a worktree, see `harness-dispatch-agents`).
- Commit: `<type>(<scope>): <summary>` in the imperative, under 72 characters. Types: feat, fix, docs, refactor, test, chore, build, ci. End with the attribution line the session gives (`Co-Authored-By: ...`).
- One logical change per commit: mod code, harness code, scenarios, tests, docs and notes are separate commits when they can stand alone.
- Add each user-visible change to `CHANGELOG.md` under `Unreleased` (Added, Changed, Deprecated, Removed, Fixed, Security), in the same commit as the change.
- When a note changes a decision, update the spec README in the same commit.

## Before you push
- Run the suites you touched. The full set: `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage` (plain venv python), and `test_fakegame_*`, `test_telemetry_mock`, `lua_syntax.py`, `boot_state_machine.py` (through `uv run --no-project --with lupa python ...`). Also `coverage.py --check-spec`.
- Look at `git status` and `git diff --stat`. Nothing from `modtools/`, `runs/`, `slots/`, `harness/pakmod.local.json`, game assets or extracts may be staged. Never `git add -A` blindly after a merge conflict: check that no conflict markers (`<<<<<<<`) remain (`grep -c "^<<<<<<<"`).
- Grep the diff for the AES key hex (read it from `modtools/work/aes_key.txt` into a shell variable; do not print it).
- Never force push. Never skip hooks. If you committed something wrong that is not pushed, fix it with a new commit or reset your own local commits; if it was pushed, merge forward.

## Pull request
`gh` is not on the PATH of the shells. Use `C:\Program Files\GitHub CLI\gh.exe`.
- Write the body to a file and use `--body-file` (quoting inline bodies breaks). Sections: Summary, Test results, Not verified. End with the line the session gives (`🤖 Generated with [Claude Code](https://claude.com/claude-code)`).
- `gh pr create --base main --head <branch> --title "<commit style title>" --body-file <file>`, then `gh pr merge <branch-or-number> --merge`.
- If GitHub says "not mergeable" right after you pushed a merge, wait a few seconds and check `gh pr view <n> --json mergeable,mergeStateStatus`.
- After the merge: `git checkout main && git pull`.

## Merge conflicts
`git merge origin/main` into your branch. The usual conflicts: `CHANGELOG.md` and the scenario list in `harness/tests/test_runlib_scenario.py` (keep both sides; rebuild the sorted list), `HarnessActions/Scripts/main.lua` (keep both requires and both command tables, bump no VERSION twice), `criteria.json` (keep the verified marks of both sides), `docs/specs/10-invasion-testability/README.md` (keep both status lines). Keep the file's line endings (many files are CRLF; write with bytes, not text mode, in scripts). Rerun the tests after resolving.

## Worktree hygiene
Remove a temporary worktree after its PR is merged (`git worktree remove --force <path>`; remove a `.venv` junction first with `cmd /c rmdir`). Do not leave a worktree on a branch the main checkout needs.
