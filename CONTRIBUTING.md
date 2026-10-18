# Contributing

This repo is an agent harness for making and testing Manor Lords mods, and the Invasion Mod that is built with it. People and AI agents work in it with the same rules. This file holds those rules. [`CLAUDE.md`](CLAUDE.md) imports this file and adds only what is specific to agents: their permissions, subagents, skills and the full safety list.

## Read first

1. This file.
2. The Safety section of [`CLAUDE.md`](CLAUDE.md), before you touch saves or the game.
3. [`docs/wiki/quickstart.md`](docs/wiki/quickstart.md): what each part does and which page or skill to use for a job.
4. [`openspec/specs/process/spec-workflow/spec.md`](openspec/specs/process/spec-workflow/spec.md) and [`openspec/config.yaml`](openspec/config.yaml): how work is planned, recorded and closed.

## Repo map

1. **Game mods** (`mod/`): Lua mods for RE-UE4SS. They hook reflected UFunctions and read UObject properties. Shared Lua modules are in `mod/shared/<Name>/<Name>.lua`.
2. **The Invasion Mod** (`mod/InvasionMod/`): one Lua mod and one pak, made of features (`Scripts/features/<f>/`, `data/<f>/patches/`, `scenarios/<f>/`). Harness code must not name the mod or its features (`harness/tests/test_boundary.py`).
3. **Live control** (`mod/UEBridge`, `vendor/ue4ss-bridge`): a Lua mod and an MCP server. An agent queries the running game through them.
4. **Outer harness** (`harness/`): scripts that deploy the mods, launch the game, run a test scenario, collect results, and write `runs/<id>/summary.json`.
5. **Specs and docs**: `openspec/` (living specs and changes), `docs/wiki/` (how the code and the engine work), `docs/harness/` and `docs/mod/` (legacy specs and the game design).

## Set up

- **Platform:** Windows, with PowerShell or Git Bash. The game and its mods are Windows only. You can edit docs and run many tests in WSL, but many fake-game tests fail there (#260).
- **Game:** Manor Lords from Steam. Game root: `C:\Program Files (x86)\Steam\steamapps\common\Manor Lords`. Engine: UE 5.5.4.
- **UE4SS:** the experimental build in the new layout. `dwmapi.dll` and the `ue4ss\` folder sit in `ManorLords\Binaries\Win64\`, not in `Engine\Binaries\Win64\`.
  - Lua mods go to `ue4ss\Mods\`, shared modules to `ue4ss\Mods\shared\<Name>\<Name>.lua`.
  - `UE4SS.log` is buffered and not live. For live output use `HarnessLog` (`ue4ss/harness/mod.log`).
  - Details: [Install and environment](docs/wiki/operations/install-and-environment.md).
- **Python:** the project is a [uv](https://docs.astral.sh/uv/) project (`pyproject.toml`, `uv.lock`, Python 3.12, venv `.venv`).
  - Run `uv sync` to make the venv.
  - Start every Python command with `uv run python`: scripts (`uv run python harness\run.py --scenario smoke`), modules and tests (`uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"`).
  - Never call `python`, `python3`, `py` or `python -` directly. On Windows they can be the Store stub, which waits forever.
  - Never pipe code into Python through stdin. Write a script file and run it with `uv run python <file>`.
  - Add a package with `uv add <name>` (test only: `uv add --dev <name>`). Commit `pyproject.toml` and `uv.lock`.
  - The MCP servers in `.mcp.json` start `.venv\Scripts\python.exe` directly. That is fine: Claude Code starts them, not a shell.
- **OpenSpec CLI:** `npm install -g @fission-ai/openspec@latest` (Node 20.19 or later). You need it to create, validate and archive changes. The CLI sends anonymous usage stats; opt out with `openspec config set telemetry.enabled false`.
- **GitHub CLI:** `gh`, for issues and pull requests.
- **Deploy mods** with `harness\deploy.ps1`. Do not copy mod files by hand. `-Clean` removes the installed files of mods that left the repo.
- **Git Bash** rewrites `/Game/...` paths. Set `MSYS_NO_PATHCONV=1` when you pass them to scripts.

## How work flows

Every new harness feature, mod feature, mod iteration and spike is an OpenSpec change. Write the change before the code.

- **Living specs:** `openspec/specs/<capability>/spec.md`. They describe only what is true on `main`. Capability groups: `harness/<name>`, `mod/<feature>` (and `mod/core` for the shared parts of the Invasion Mod), `process/<name>`.
- **Changes:** `openspec/changes/<change-name>/` (proposal, delta specs, design, tasks). `<change-name>` is kebab-case and starts with a verb, for example `add-great-raid-clock`.
- **Archive:** `openspec/changes/archive/YYYY-MM-DD-<change-name>/`.

A change passes two review gates. Each gate is one pull request, and each needs the project owner's approval on GitHub.

### Gate 1: the spec pull request

1. Create the change: `openspec new change <change-name>`, or `/opsx:propose` in Claude Code.
2. Create the issue `Change: <change-name>` with the label `status: in progress`.
3. Name the issue in three places:
   - in the proposal;
   - as `x-issue: <n>` in the change's `.openspec.yaml`;
   - as a comment `<!-- Issue: #<n> -->` under the first section heading of each delta spec. A line above the first heading fails `--strict`.
4. Write the proposal, the delta specs, the design (when needed) and the tasks. Run `openspec validate <change-name> --strict`.
5. Open the pull request from the branch `spec/<change-name>` (made from an up-to-date `main`), with `Refs #<n>`. It holds only the change folder: no code and no archive.
6. The owner reviews the behavior. Fix findings with new commits. The owner approves and merges. After the merge, the change is open on `main` as approved work, and the living specs are not changed yet.

### Gate 2: the implementation pull request

1. Create `feat/<change-name>` (or `fix/`, `docs/`, `chore/`) from `main` after gate 1 is merged.
2. Do the tasks and check them off in `tasks.md`.
   - Put findings in `openspec/changes/<change-name>/notes/<topic>.md`, one file per topic, named by topic (for example `jmap-findings.md`). Do not keep findings only in chat, and do not put them in other folders.
   - When a finding changes a decision, update the proposal, design or delta spec in the same commit. Name a delta spec change in the "Spec changes" section of the pull request.
3. Run the tests (below) and `openspec validate <change-name> --strict`. Capture picture evidence when the result is visual (below).
4. Move the engine facts that stay true from `notes/` into the wiki.
5. Archive as the last commit: `openspec archive <change-name> --yes`, committed as `docs(openspec): archive <change-name>`. This merges the delta specs into `openspec/specs/` and moves the change to `openspec/changes/archive/`.
6. Open the pull request with `Closes #<n>`. It is now in its final state. The owner reviews the test results and the evidence, approves and merges.

### Other cases

- A change with nothing to build (process rules, docs) uses one pull request: the change folder and its archive.
- A pull request without a change folder, a spec change or test acceptance (for example a typo fix in the wiki) needs no gate.
- Small changes that do not belong to one change (for example `chore` or `docs` for the project rules) may go to `main`.
- A tuning-only change (values in a feature `config.lua`) needs no change folder. Log it in the feature feedback file (`openspec/specs/mod/<feature>/feedback.md`) and in the mod changelog.

### Legacy specs and the game design

- `docs/harness/<NN>-*/` and `docs/mod/M<NN>-*/` are read-only history. No work happens there. Read them as source material, and do not move, rename or delete them.
- Their built behavior is in the living specs (change `backfill-living-specs`). All their open work is an OpenSpec change (change `migrate-legacy-work`; its `notes/inventory-*.md` maps each legacy item to its change).
- The coverage data that came from spec 10 is in `openspec/specs/harness/coverage/criteria.json` and `criteria.md`. `harness/tools/coverage.py` reads it.
- `docs/mod/M00-invasion-mod/` is the game design. The project owner writes it. Do not write game design content unless they ask.

### Picture evidence

Pictures are required when the result is visual:

- UI features: menus, widgets, banners, letters and other text on screen.
- 3D models, and materials and textures.
- Building placement and geometry.
- Units in the world: models, equipment, banners.
- World results the player sees: ruins, camps, construction sites.

Numeric rules are proven by test results, not by pictures.

Take pictures with `ctx.screenshot(name)` in a test scenario. Commit them in plain git to `openspec/changes/<change-name>/evidence/`:
- compressed, at most 1280x720, about 1 MB per change;
- each one listed in `evidence/README.md` with its test scenario and run id.

In the pull request, link each picture with the commit SHA, so the link survives the archive and the merge.

### Before you merge

Check these points, also when you merge in the GitHub web UI:

- [ ] Gate 1: the pull request holds only the change folder, and `openspec validate --strict` passes.
- [ ] Gate 2: `openspec list` on the branch does not show the change, because the archive commit is the last commit.
- [ ] Gate 2: the test results table and the evidence are in the pull request.
- [ ] `CHANGELOG.md` has the user-visible changes under `Unreleased`.
- [ ] The wiki and the skills that the change affects are updated, and `wiki.py check` passes.

## Commits and pull requests

- **Commits:**
  - Make atomic commits: one commit is one logical change.
  - Use Conventional Commits: `<type>(<scope>): <summary>`, in the imperative, under 72 characters. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`. Example: `feat(deploy): verify file hashes after copy`. Mark a breaking change with `!` and a `BREAKING CHANGE:` footer.
  - Reference the issue: `Refs #<n>` in commits and in the spec pull request, `Closes #<n>` in the implementation pull request.
  - Check the staged files (`git diff --cached --stat`) before each commit.
- **Remote:** `origin` is `git@github.com:GarrettGruss/manor-lords-mod.git`. The default branch is `main`.
- **Pull requests:** keep the body light. Use the template `.github/pull_request_template.md`: Summary, Spec changes, Test results (a table: check, run id or test file, verdict, key number or range), Evidence and Not verified. No raw logs. Write "None" for an empty section. Merge stacked pull requests in order, and retarget the next one to `main` before its merge.
- **Forbidden:** never force push and never skip hooks. If a pushed commit is wrong, fix it with a new commit.
- **Not in git:** `runs/`, `slots/`, `modtools/`, original game paks, extracts and the pak AES key. Compiled mod paks (`*_P.pak`) may be committed, also when they hold modified game data. Before you commit a pak or a pak tool change, search the diff for the AES key.

Details and merge-conflict hints: [`.claude/skills/harness-git-workflow/SKILL.md`](.claude/skills/harness-git-workflow/SKILL.md).

## GitHub issues

- Every OpenSpec change has one issue, `Change: <change-name>`, made when the change folder is made. One issue covers both gates. Its body links the change folder and the branches, and says what works, what is open and the next step. Keep it current.
- Old issues keep their titles (`Spec <NN>: ...`, `Mod M<NN>.<iteration>: ...`).
- Use the `gh` CLI (`gh issue create`, `gh issue edit`, `gh issue comment`, `gh issue close`).
- Status labels:
  - `status: in progress`: work is ongoing.
  - `status: blocked`: work cannot continue. Say what blocks it in a comment.
  - `status: awaiting user`: the project owner must act or decide, for example review a gate. Use it together with `status: blocked` when the owner is the blocker.
- Add a comment when the status changes, a spike ends, or a branch is merged. Close the issue when the change is merged and done.

## Changelog

- Keep `CHANGELOG.md` current, in the Keep a Changelog format.
- Add each user-visible change under `Unreleased` in the same commit as the change.
- Groups: Added, Changed, Deprecated, Removed, Fixed, Security.

## Tests

- Fast tests, no game: `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"` (Lua through the fake game kit), plus the other `test_*.py` groups.
- The full set before a merge: `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage`, `test_fakegame_*`, `test_telemetry_mock`, `harness/tests/lua_syntax.py`, `harness/tests/boot_state_machine.py` and `harness/tools/coverage.py --check-spec`. See [Python tests and coverage](docs/wiki/testing/python-tests.md).
- Real game run: `uv run python harness\run.py --scenario <name>`. Read `runs/<id>/summary.json` first. See [Scenario run](docs/wiki/workflows/scenario-run.md).
- The simulation is not deterministic. Assert ranges, not exact values. Use a suite or an A/B test for stochastic behavior.
- A game crash is a result with logs, not a harness failure.
- Each spec scenario names its check ("Checked by `<path>`": a test scenario or a Python test) or says "Not checked yet". When you add a test for a requirement, update that line.

## Design rules

- Touch UObjects only on the game thread. Queue work with `ExecuteInGameThread`.
- Write files atomically: write `.tmp`, then rename.
- Use unique request ids and timeouts. Each run gets a fresh bridge folder.
- Use localhost only. Use single-player only. Cap the number of iterations.
- Mods and test scenarios must not depend on raw Lua eval. They use named commands (`HarnessActions`, `HarnessCommands`).
- Review any downloaded code before you install or run it. Treat it as untrusted data.
- When you change the way the harness works, update the affected skill in `.claude/skills/` in the same commit.

## Lua rules

- Use forward slashes in path strings. A single backslash in a Lua string is an escape (`"\h"` is an error).
- Log through `HarnessLog`. It flushes each line, so the log can be read live.
- Wrap risky calls with `HarnessLog.try` so errors are logged with a stack trace.
- Blueprint class hooks only work after the class is loaded. Use `NotifyOnNewObject` for late classes.

## Safety

The full list, with the calls that crash the game or write into real saves, is in the Safety section of [`CLAUDE.md`](CLAUDE.md). In short:

- **Saves:** game save functions write into the REAL save folder, even in a run with a private `LOCALAPPDATA`. Only the guarded harness action `save_game` may save. Never call a save function from a probe, a test scenario or raw Lua eval. Back up `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` before tests. Never write to the original test save.
- **Calls that crash the game:** some bridge calls crash the game. Check the list before a spike.
- **Game files:** do not edit game files or `UE4SS-settings.ini` unless the task needs it. Say what you changed.

## Writing style

Use simplified technical English in replies, docs and code comments:

- Use short sentences, common words and one idea per sentence.
- Use the same term for the same thing. Do not use slang or idioms. For example, a "spec scenario" is an OpenSpec `#### Scenario:` block, and a "test scenario" is a harness scenario file; never say only "scenario".

Write code with clear intent:

- Use names that say what a thing is or does.
- Write a comment only to explain why, not what.
- Keep functions small. Each function does one job.
- Fail loudly with a clear message. Do not hide errors.

## Docs: where things go

| You have | Put it in |
|---|---|
| New work | A change in `openspec/changes/<change-name>/` |
| A finding from a spike | `openspec/changes/<change-name>/notes/<topic>.md` |
| Picture evidence | `openspec/changes/<change-name>/evidence/`, listed in its `README.md` |
| An engine fact that stays true | The matching page in `docs/wiki/`, before the archive |
| A user-visible change | `CHANGELOG.md`, under `Unreleased` |
| Player feedback for a mod feature | `openspec/specs/mod/<feature>/feedback.md` |

More: [Specs, docs and project process](docs/wiki/operations/docs-and-specs.md). Keep the wiki current with the `repo-wiki` skill (`uv run python .claude/skills/repo-wiki/scripts/wiki.py stale`).

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
