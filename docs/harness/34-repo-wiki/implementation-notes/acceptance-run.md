# Acceptance run (init, 2026-10-18)

The skill `repo-wiki` ran an init over the repo on branch `feat/34-repo-wiki`, in a WSL (Linux) shell.

## What ran
1. Explore: CLAUDE.md, `harness-overview`, `harness/README.md`, `docs/mod/README.md`, `mcp/README.md`, the folder tree.
2. Plan: 23 pages plus `quickstart.md` in six folders (`architecture`, `concepts`, `integrations`, `operations`, `testing`, `workflows`).
3. Pages: 9 Sonnet subagents in parallel, two or three pages each, with the prompt from the skill. Time: about 1.5 to 7.5 minutes per agent. The main session wrote `quickstart.md`.
4. `wiki.py index` wrote 7 indexes. The first `wiki.py check` after the quickstart reported `wiki check: ok`. The agents had used `check` on their own pages before.
5. Review: two to five facts for each page, checked against the source (constants, file names, state names, dependencies, test names).
6. `wiki.py stamp --command init`.

## Result against the criteria
| Criterion | Result |
|---|---|
| 1 unit tests | `test_wiki_tool.py`: 16 tests pass |
| 2 init writes the wiki | 24 pages, about 2,500 lines. They cover `mod/`, `harness/`, `mcp/`, `docs/` |
| 3 check is clean | `wiki check: ok` |
| 4 stale | After `stamp`: 0 stale pages, 0 uncovered paths. `stale --since HEAD~10`: 68 changed paths, 15 stale pages, 0 uncovered |
| 5 skill and overview | `repo-wiki` skill; `harness-overview` and CLAUDE.md name it |

`test_boundary.py`, `test_save_call_sites.py` and `coverage.py --check-spec` still pass with the new files.

## Review corrections
Subagent pages were mostly right. The review changed these:
- `overview.md`: "bridge folders are wiped at launch" became "each run gets a new `runs/<id>/bridge/` folder" (`runfolder.py`).
- `scenario-run.md`: "the game save folder is never written by the game" was wrong. Now: only the installed slot is added and removed; any other change fails teardown.
- `suites-and-ab.md`: a test command used the module form `harness.tests.test_runlib_series`, but `harness/tests` is not a package; and "runs never touch the real save folder" was wrong (fixtures are installed there).
- `dev-loop-and-fixtures.md`: "commit the manifest entry only" was the agent's own advice; now it states the fact (the saves folder is git-ignored).
- `other-mods.md`: the stand-in header says "deploy only for stand-in scenarios", but `deploy.ps1` deploys every folder. The page now says both.
- `shared-lua-modules.md`: a test file name (`test_fakegame_modstate.py`).
- `fake-game-kit.md`, `python-tests.md`: the agent wrote dated test counts of this shell into the pages. They were replaced by the stable cause (below).

## Findings
- **Fake-game tests on Linux.** `HarnessLog` makes folders with Windows `mkdir` and `>nul`. On Linux the test run of a subagent left 3,909 empty folders named `\tmp\fakegame-*`, a file `nul` and `runs/.saves.lock` in the repo root. They were removed. Many `test_fakegame_*` tests fail on Linux for this reason. Recorded in `docs/wiki/testing/fake-game-kit.md`. Not fixed here (out of scope).
- **Broad sources make pages always stale.** `source-map.md` lists `harness/`, `mod/`, `docs/`, so 67 of 68 changed paths hit it. That is right for a map page, but `stale` output gets long. A later change could let `stale` group pages by how many sources hit, or the skill could ask for narrower sources. Not changed now.
- **Subagents verify their own links.** Agents ran `wiki.py check` while the others still wrote, so the only early errors were links to unwritten pages. This worked well with no extra rule.
- **Session facts creep in.** One agent wrote shell-specific test results into two pages. The skill got a rule in "Page quality": write facts about the system, not about the session.
