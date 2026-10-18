---
name: harness-git-workflow
description: Branch, commit, push, open and merge pull requests for this repo, and handle changelog and merge conflicts. Use whenever you finish a piece of work in the manor-lords-mod repo.
---

# Git workflow for this repo

Rules are in CLAUDE.md: atomic Conventional commits, two review gates per OpenSpec change, CHANGELOG kept current. Gate 1 is a spec pull request, gate 2 an implementation pull request; the user approves and merges both on GitHub. Do not merge a gate pull request yourself. A pull request without a gate (no change folder, no spec change, no test acceptance) may be merged by you after the full tests pass (CLAUDE.md, Git).

## Branch and commit
- Gate 1: branch `spec/<change-name>` from an up-to-date `main`. Commit only the change folder (proposal, delta specs, design, tasks). No code, no archive.
- Gate 2: branch `feat/<change-name>` (or `fix/`, `docs/`, `chore/`) from `main` after gate 1 is merged (or a worktree, see `harness-dispatch-agents`). A change with nothing to build uses one branch and one pull request. Open legacy work keeps its old branch (`feat/<NN>-<name>`, `feat/M<NN>-<feature>-<iteration>`).
- Commit: `<type>(<scope>): <summary>` in the imperative, under 72 characters. Types: feat, fix, docs, refactor, test, chore, build, ci. End with the attribution line the session gives (`Co-Authored-By: ...`).
- One logical change per commit: mod code, harness code, scenarios, tests, docs and notes are separate commits when they can stand alone.
- A releasable mod has its own `mod/<Name>/CHANGELOG.md` and `mod.json`. Change them in the same commit as a mod change that players see (skill `harness-release`).
- Add each user-visible change to `CHANGELOG.md` under `Unreleased` (Added, Changed, Deprecated, Removed, Fixed, Security), in the same commit as the change.
- When a note changes a decision, update the proposal, design or delta spec of the change in the same commit.

## Before you push
- Run the suites you touched. The full set: `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage` (plain venv python), and `test_fakegame_*`, `test_telemetry_mock`, `lua_syntax.py`, `boot_state_machine.py` (through `uv run python ...`). Also `coverage.py --check-spec`.
- Run `openspec validate <change-name> --strict`.
- Look at `git status` and `git diff --stat`. Nothing from `modtools/`, `runs/`, `slots/`, `harness/pakmod.local.json`, original game paks, extracts, `.usmap` files or the AES key may be staged (compiled mod paks `*_P.pak` may be staged; grep the diff for the key first). Never `git add -A` blindly after a merge conflict: check that no conflict markers (`<<<<<<<`) remain (`grep -c "^<<<<<<<"`).
- Grep the diff for the AES key hex (read it from `modtools/work/aes_key.txt` into a shell variable; do not print it). In a worktree the file is in the main checkout: `C:\Users\garre\development\manor-lords-mod\modtools\work\aes_key.txt`.
- Never force push. Never skip hooks. If you committed something wrong that is not pushed, fix it with a new commit or reset your own local commits; if it was pushed, merge forward.

## Pull request
`gh` is not on the PATH of the shells. Use `C:\Program Files\GitHub CLI\gh.exe`.
- Write the body to a file and use `--body-file` (quoting inline bodies breaks). Follow `.github/pull_request_template.md`: Summary, Spec changes, Test results (a table: check, run id or test file, verdict, key number or range), Evidence, Not verified. No raw logs; "None" for an empty section. End with the line the session gives (`🤖 Generated with [Claude Code](https://claude.com/claude-code)`).
- Gate 1: `gh pr create --base main --head spec/<change-name> ...` with `Refs #<n>`. Then mark the issue `status: awaiting user` and stop. Do not start gate 2 before the user merges.
- Gate 2: before you open the pull request, finish it: run the full tests, put picture evidence in `evidence/` when the result is visual, move lasting engine facts from `notes/` into the wiki, run `openspec archive <change-name> --yes`, check the merged living spec, commit `docs(openspec): archive <change-name>` and push. Then `gh pr create ... --body-file <file>` with `Closes #<n>`, and mark the issue `status: awaiting user`.
- Link pictures with the commit SHA: `https://github.com/GarrettGruss/manor-lords-mod/raw/<sha>/openspec/changes/archive/<date>-<change-name>/evidence/<file>.png`.
- `gh pr edit` fails on this repo (a GraphQL error about classic projects). Change a body with `gh api -X PATCH repos/GarrettGruss/manor-lords-mod/pulls/<n> -F "body=@<file>"`.
- Merge only a pull request without a gate: `gh pr merge <branch-or-number> --merge`. If GitHub says "not mergeable" right after you pushed a merge, wait a few seconds and check `gh pr view <n> --json mergeable,mergeStateStatus`.
- After a merge: `git checkout main && git pull`. If a gate 2 pull request was merged without its archive commit, archive on a new branch as its own commit.

## Merge conflicts
`git merge origin/main` into your branch. The usual conflicts: `CHANGELOG.md` and the scenario list in `harness/tests/test_runlib_scenario.py` (keep both sides; rebuild the sorted list), `HarnessActions/Scripts/main.lua` (keep both requires and both command tables, bump no VERSION twice), `criteria.json` (keep the verified marks of both sides), `docs/harness/10-invasion-testability/README.md` (keep both status lines). Keep the file's line endings (many files are CRLF; write with bytes, not text mode, in scripts). Rerun the tests after resolving.

## Worktree hygiene
Remove a temporary worktree after its PR is merged (`git worktree remove --force <path>`; remove a `.venv` junction first with `cmd /c rmdir`). Do not leave a worktree on a branch the main checkout needs.
