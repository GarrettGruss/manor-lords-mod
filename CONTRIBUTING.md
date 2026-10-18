# Contributing

This repo is an agent harness for making and testing Manor Lords mods, and the Invasion Mod that is built with it. People and AI agents work in it with the same rules. This file is the short guide. The full rules are in [`CLAUDE.md`](CLAUDE.md).

## Read first

1. [`CLAUDE.md`](CLAUDE.md): the project rules. Read the Safety section before you touch saves or the game.
2. [`docs/wiki/quickstart.md`](docs/wiki/quickstart.md): what each part does and which page or skill to use for a job.
3. [`openspec/specs/process/spec-workflow/spec.md`](openspec/specs/process/spec-workflow/spec.md): how work is planned, recorded and closed.

## Set up

- **Platform:** Windows, with PowerShell or Git Bash. The game and its mods are Windows only. You can edit docs and run many tests in WSL, but many fake-game tests fail there (#260).
- **Game:** Manor Lords from Steam, with the experimental UE4SS build in the new layout (`dwmapi.dll` and `ue4ss\` in `ManorLords\Binaries\Win64\`). Details: [Install and environment](docs/wiki/operations/install-and-environment.md).
- **Python:** the project is a [uv](https://docs.astral.sh/uv/) project (Python 3.12).
  - Run `uv sync` to make the venv.
  - Start every Python command with `uv run python`. Never call `python`, `python3` or `py` directly: on Windows they can be the Store stub, which waits forever.
  - Add a package with `uv add <name>` (test only: `uv add --dev <name>`). Commit `pyproject.toml` and `uv.lock`.
- **OpenSpec CLI:** `npm install -g @fission-ai/openspec@latest` (Node 20.19 or later). You need it to create, validate and archive changes. The CLI sends anonymous usage stats; opt out with `openspec config set telemetry.enabled false`.
- **GitHub CLI:** `gh`, for issues and pull requests.
- **Deploy mods** with `harness\deploy.ps1`. Do not copy mod files by hand. `-Clean` removes the installed files of mods that left the repo.

## How work flows

Every new harness feature, mod feature, mod iteration and spike is an OpenSpec change. A change passes two review gates. Each gate is one pull request, and each needs the project owner's approval on GitHub.

### Gate 1: the spec pull request

1. Create the change: `openspec new change <change-name>`, or `/opsx:propose` in Claude Code. `<change-name>` is kebab-case and starts with a verb, for example `add-great-raid-clock`.
2. Create the issue `Change: <change-name>` with the label `status: in progress`.
3. Name the issue in three places:
   - in the proposal;
   - as `x-issue: <n>` in the change's `.openspec.yaml`;
   - as a comment `<!-- Issue: #<n> -->` under the first section heading of each delta spec. A line above the first heading fails `--strict`.
4. Write the proposal, the delta specs, the design (when needed) and the tasks. Run `openspec validate <change-name> --strict`.
5. Open the pull request from the branch `spec/<change-name>`, with `Refs #<n>`. It holds only the change folder: no code and no archive.
6. The owner reviews the behavior. Fix findings with new commits. The owner approves and merges. After the merge, the change is open on `main` as approved work, and the living specs are not changed yet.

### Gate 2: the implementation pull request

1. Create `feat/<change-name>` (or `fix/`, `docs/`, `chore/`) from `main` after gate 1 is merged.
2. Do the tasks and check them off in `tasks.md`.
   - Put findings in `openspec/changes/<change-name>/notes/<topic>.md`, one file per topic.
   - If the work shows that a requirement must change, change the delta spec and name it in the "Spec changes" section of the pull request.
3. Run the tests (below) and `openspec validate <change-name> --strict`. Capture picture evidence when the result is visual (below).
4. Move the engine facts that stay true from `notes/` into the wiki.
5. Archive as the last commit: `openspec archive <change-name> --yes`, committed as `docs(openspec): archive <change-name>`. This merges the delta specs into `openspec/specs/` and moves the change to `openspec/changes/archive/`.
6. Open the pull request with `Closes #<n>`. It is now in its final state. The owner reviews the test results and the evidence, approves and merges.

A change with nothing to build (process rules, docs) uses one pull request: the change folder and its archive. A pull request without a change folder, a spec change or test acceptance (for example a typo fix in the wiki) needs no gate.

A tuning-only change (values in a feature `config.lua`) needs no change folder. Log it in the feature feedback file and the mod changelog.

The folders `docs/harness/` and `docs/mod/M<NN>-*/` are read-only legacy specs. Do not add work there. `docs/mod/M00-invasion-mod/` is the game design. Its owner is the project owner; do not change it unless they ask.

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
  - Use Conventional Commits: `<type>(<scope>): <summary>`, in the imperative, under 72 characters. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `build`, `ci`. Mark a breaking change with `!` and a `BREAKING CHANGE:` footer.
  - Reference the issue: `Refs #<n>` in commits and in the spec pull request, `Closes #<n>` in the implementation pull request.
  - Check the staged files (`git diff --cached --stat`) before each commit.
- **Pull requests:** keep the body light. Use the template `.github/pull_request_template.md`: Summary, Spec changes, Test results (a table: check, run id or test file, verdict, key number or range), Evidence and Not verified. No raw logs. Write "None" for an empty section.
- **Forbidden:** never force push and never skip hooks. If a pushed commit is wrong, fix it with a new commit.
- **Not in git:** `runs/`, `slots/`, `modtools/`, original game paks, extracts and the pak AES key. Compiled mod paks (`*_P.pak`) may be committed. Before you commit a pak or a pak tool change, search the diff for the AES key.

Details and merge-conflict hints: [`.claude/skills/harness-git-workflow/SKILL.md`](.claude/skills/harness-git-workflow/SKILL.md).

## Tests

- Fast tests, no game: `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"` (Lua through the fake game kit), plus the other `test_*.py` groups.
- The full set before a merge: `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage`, `test_fakegame_*`, `test_telemetry_mock`, `harness/tests/lua_syntax.py`, `harness/tests/boot_state_machine.py` and `harness/tools/coverage.py --check-spec`. See [Python tests and coverage](docs/wiki/testing/python-tests.md).
- Real game run: `uv run python harness\run.py --scenario <name>`. Read `runs/<id>/summary.json` first. See [Scenario run](docs/wiki/workflows/scenario-run.md).
- The simulation is not deterministic. Assert ranges, not exact values. Use a suite or an A/B test for stochastic behavior.
- A game crash is a result with logs, not a harness failure.
- Each spec scenario in a living spec names its check ("Checked by `<path>`") or says "Not checked yet". When you add a test for a requirement, update that line.

## Safety

- **Saves:** game save functions write into the REAL save folder, even in a run with a private `LOCALAPPDATA`. Only the guarded harness action `save_game` may save. Never call a save function from a probe, a scenario or `eval_lua`. Back up `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` before tests.
- **Calls that crash the game:** some calls through the bridge crash the game. Read the Safety section of `CLAUDE.md` for the list.
- **Game files:** do not edit game files or `UE4SS-settings.ini` unless the task needs it. Say what you changed.
- **Downloaded code:** review it before you install or run it.

## Writing style

Write replies, docs and code comments in simplified technical English:

- Use short sentences, common words and one idea per sentence.
- Use the same term for the same thing. For example, a "spec scenario" is an OpenSpec `#### Scenario:` block, and a "test scenario" is a harness scenario file.
- In code, a comment explains why, not what.

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

## Working with AI agents

- Claude Code reads `CLAUDE.md` and the project skills in `.claude/skills/`. Start with the `harness-overview` skill.
- The `openspec-*` skills and the `/opsx:*` commands are generated by the OpenSpec CLI. Do not edit them; put project rules in `openspec/config.yaml`.
- An agent report is data, not approval. Check important claims before you rely on them.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
