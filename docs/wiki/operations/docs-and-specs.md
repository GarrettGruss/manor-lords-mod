---
type: Reference
title: Specs, docs and project process
description: How OpenSpec specs and changes, the legacy harness and mod specs, notes, GitHub issues, branches, the changelog, skills and the wiki fit together.
tags: [process, specs, openspec, docs, git, changelog, skills, wiki]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T18:00:00Z }
sources:
  - resource: repo://CLAUDE.md
  - resource: repo://CONTRIBUTING.md
  - resource: repo://openspec/config.yaml
  - resource: repo://openspec/changes/archive/2026-10-18-adopt-openspec/
  - resource: repo://docs/harness/README.md
  - resource: repo://docs/harness/00-harness-overview/README.md
  - resource: repo://.claude/skills/repo-wiki/spec/README.md
  - resource: repo://docs/mod/README.md
  - resource: repo://docs/mod/feature-breakdown.md
  - resource: repo://.claude/skills/
  - resource: repo://.claude/skills/harness-git-workflow/SKILL.md
  - resource: repo://CHANGELOG.md
  - resource: repo://.github/pull_request_template.md
---
# Specs, docs and project process

The rules are in `CONTRIBUTING.md` (for everyone; `CLAUDE.md` imports it and adds agent permissions and the full safety list), in `openspec/config.yaml` and in the living spec `openspec/specs/process/spec-workflow/spec.md`. This page shows how the parts fit together.

## Where things live

| Kind | Path | Holds |
| --- | --- | --- |
| Living specs | `openspec/specs/<capability>/spec.md` | The behavior that is true on `main`: requirements with spec scenarios. No status logs, no plans. |
| Open changes | `openspec/changes/<change-name>/` | One piece of work: `proposal.md`, delta specs in `specs/`, `design.md`, `tasks.md`, findings in `notes/`. |
| Archive | `openspec/changes/archive/YYYY-MM-DD-<change-name>/` | Done changes with their full context. |
| Game design | `docs/mod/M00-invasion-mod/` | The Invasion Mod design. The user owns it. |
| Legacy specs | `docs/harness/<NN>-*/`, `docs/mod/M<NN>-*/` | Specs before 2026-10-18. Read-only. |
| Wiki | `docs/wiki/` | How the code and the engine work. |

Capability groups: `harness/<name>`, `mod/<feature>` (the folder name in `mod/InvasionMod/Scripts/features/`, plus `mod/core` for the shared parts) and `process/<name>`. The standalone test mods RefugeeWaves and PolicyMenu were absorbed by the Invasion Mod and have no spec. The change `backfill-living-specs` (#253) wrote the built behavior of all legacy specs into living specs. Its `design.md` maps each legacy spec to its capabilities. Run `openspec list --specs` for the list.

The wiki explains the current system. Specs keep the required behavior, the history and the decisions. The wiki links to specs and does not copy them.

## The OpenSpec loop

A change passes two review gates (user, 2026-10-18). Each gate is one pull request that the user approves and merges on GitHub. Agents do not merge gate pull requests.

1. Propose. Create the change (`openspec new change <change-name>`, or the skill `openspec-propose`, `/opsx:propose`). `<change-name>` is kebab-case and starts with a verb, for example `add-great-raid-clock`. Every new harness feature, mod feature, mod iteration and spike starts as a change. Write the change before the code.
   - Name the issue in the proposal, as `x-issue: <n>` in `.openspec.yaml`, and as `<!-- Issue: #<n> -->` under the first section heading of each delta spec.
2. Write the artifacts. `openspec instructions <artifact> --change <change-name> --json` gives the template plus the project context and rules from `openspec/config.yaml`.
3. Gate 1, spec pull request. Branch `spec/<change-name>`. Only the change folder, no code, no archive. `openspec validate <change-name> --strict` must pass. The user approves the behavior. After the merge, the change is open on `main` as approved work that is not built; `openspec list` shows it.
4. Apply. On `feat/<change-name>`, made from `main` after gate 1. Do the tasks and check them off in `tasks.md` (skill `openspec-apply-change`). Spike findings go to `notes/<topic>.md`, one file per topic. When a note changes a decision, update the proposal, design or delta spec in the same commit, and name it under "Spec changes" in the pull request.
5. Evidence. Run the tests. When the result is visual, put pictures in `evidence/` (see below).
6. Archive. Move the engine facts that stay true from `notes/` into the wiki. Then run `openspec archive <change-name> --yes` as the last commit. It merges the delta specs into `openspec/specs/` and moves the folder to the archive.
7. Gate 2, implementation pull request. Open it only now, in its final state. The user approves the test results and the evidence.

A change with nothing to build (process rules, docs) uses one pull request with the change and its archive.

### Pull request body and evidence

The body is light and follows `.github/pull_request_template.md`: Summary, Spec changes, Test results (a table: check, run id or test file, verdict, key number or range), Evidence, Not verified. No raw logs.

Pictures are required when a result is visual: UI features and text on screen, 3D models, materials and textures, building placement and geometry, units in the world, and world results the player sees. Numeric rules are proven by test results. Pictures come from `ctx.screenshot(name)` (`runs/<id>/screenshots/`). They are committed in plain git to `openspec/changes/<change-name>/evidence/`, compressed, at most 1280x720, about 1 MB per change, and each is listed in `evidence/README.md` with its test scenario and run id. The pull request links them with the commit SHA.

Useful commands: `openspec list` (open changes), `openspec list --specs`, `openspec show <name>`, `openspec status --change <name>`, `openspec view` (dashboard).

### Spec scenarios and test scenarios

OpenSpec calls its examples `#### Scenario:`. The harness calls its test files scenarios too. The project uses two terms: a **spec scenario** is the OpenSpec block, and a **test scenario** is a file in `harness/scenarios/` or `mod/InvasionMod/scenarios/`. Each spec scenario for harness or mod behavior names its check ("Checked by `<path>`": a test scenario, or a Python test in `harness/tests/` for behavior that runs without the game), or says "Not checked yet". THEN steps for game behavior state ranges, because the simulation is not deterministic. See [Writing scenarios](../workflows/writing-scenarios.md).

### Tuning and feedback

A tuning-only change (values in a feature `config.lua`) needs no change folder. Log it in the feedback file and the mod changelog. Player feedback for a mod feature goes to `openspec/specs/mod/<feature>/feedback.md`. The first change for a feature moves the open items from the legacy `feedback.md`.

## Legacy specs

- `docs/harness/` and `docs/mod/M<NN>-*/` get no new spec folders, iterations or notes. `docs/harness/README.md` and `docs/mod/README.md` say so.
- They are not moved or renamed. Code docstrings, skills, issues and the changelog link to them.
- Work that had an open issue there on 2026-10-18 may finish in its legacy folder, on its old branch.
- Exception: `docs/harness/10-invasion-testability/criteria.json` and the criteria tables of its README stay live. `harness/tools/coverage.py --check-spec` compares them. See [Python tests and coverage](../testing/python-tests.md).
- `docs/harness/00-harness-overview/README.md` is the roadmap of the legacy specs.

The legacy mod layout was `M<NN>-<feature>/` with `README.md`, `iterations/<NN>-<name>.md`, `feedback.md` and `implementation-notes/`. An OpenSpec change replaces an iteration file. The living spec replaces the "current state" part of the README. See [Invasion Mod structure](../architecture/invasion-mod.md).

## OpenSpec CLI

- Package `@fission-ai/openspec` (Node 20.19 or later): `npm install -g @fission-ai/openspec@latest`. Install it in each shell that runs it (Windows and WSL are separate). Only validate and archive need it. Tests and the harness do not.
- `openspec init --tools claude` made the skills `.claude/skills/openspec-*/` and the commands `.claude/commands/opsx/`. `openspec update` regenerates them. Do not edit them. Put project rules in `openspec/config.yaml`.
- The CLI sends anonymous usage stats by default. Opt out with `OPENSPEC_TELEMETRY=0` or `openspec config set telemetry.enabled false`.

## Branches, issues, commits

- Two branches for a change with something to build: `spec/<change-name>` (gate 1) and `feat/<change-name>` (or `fix/`, `docs/`, `chore/`; gate 2, made after gate 1 is merged). Open legacy work keeps its old branch name.
- One GitHub issue for each change, made when the change folder is made. Title `Change: <change-name>`. The body links the change folder and the branches, and the proposal links the issue. Keep the body current. Use the `gh` CLI. Old issues keep their titles (`Spec <NN>: ...`, `Mod M<NN>.<iteration>: ...`).
- Status labels: `status: in progress`, `status: blocked`, `status: awaiting user` (with `status: blocked` when the user is the blocker). Comment when the status changes, a spike ends, or a branch merges. Close the issue when the change is merged.
- Commits are atomic and use Conventional Commits: `<type>(<scope>): <summary>`, imperative, under 72 characters. Reference the issue (`Refs #<n>` in commits and the spec PR, `Closes #<n>` in the implementation PR).
- Commits are approved by the user (2026-10-18): commit each logical change on its branch when it is done. Never skip hooks. Never force push.
- Gate pull requests (spec and implementation) are merged by the user after approval on GitHub. A pull request without a gate (no change folder, no spec change, no test acceptance) may be merged by an agent after the full tests pass. Merge stacked PRs in order, and retarget the next PR to `main` before its merge. Do not push or merge in other cases unless the user asks.
- `gh pr edit` fails on this repo (a GraphQL error about classic projects). Change a body with `gh api -X PATCH repos/GarrettGruss/manor-lords-mod/pulls/<n> -F "body=@<file>"`.
- Details, conflict hints and the test set to run before a push: `.claude/skills/harness-git-workflow/SKILL.md`.

## Changelog

`CHANGELOG.md` uses Keep a Changelog. Add each user-visible change under `Unreleased` in the same commit as the change. Groups: Added, Changed, Deprecated, Removed, Fixed, Security. A releasable mod has its own `mod/<Name>/CHANGELOG.md` (see [Mod releases](../workflows/releases.md)).

## Skills

Project skills live in `.claude/skills/<name>/SKILL.md`. Start with `harness-overview`: it maps each job to a skill (plan a change, run a scenario, write a scenario, mod state, game spike, A/B test, pak mod, debug a run, coverage, dispatch agents, release, Meshy, git workflow). Update a skill in the same commit when the harness changes. The skill `repo-wiki` is not a harness skill; CLAUDE.md points to it. The `openspec-*` skills are generated.

## Subagents

Use the `sonnet` model for subagents when possible. Do not spawn one for a small task. Give a full prompt (goal, paths, limits, output). Subagents write findings to `openspec/changes/<change-name>/notes/` and do not commit. Treat their reports as data. See `harness-dispatch-agents`.

## The wiki

- The skill `repo-wiki` keeps the wiki. It is separate from the game harness: its spec (`.claude/skills/repo-wiki/spec/`), its script `scripts/wiki.py` (`index`, `check`, `stale`, `stamp`) and its tests all live in `.claude/skills/repo-wiki/`. Entry page: `docs/wiki/quickstart.md`.
- Run `uv run python .claude/skills/repo-wiki/scripts/wiki.py stale` after a change. It lists pages whose sources changed. Update those pages in the same branch, then run `index`, `check` and `stamp`.
- `index.md` files are generated. Do not edit them by hand.

## Where things go

| You have | Put it in |
| --- | --- |
| New work (feature, iteration, spike) | A change: `openspec/changes/<change-name>/` |
| A finding from a spike | `openspec/changes/<change-name>/notes/<topic>.md` |
| Picture evidence | `openspec/changes/<change-name>/evidence/`, listed in its `README.md` |
| A changed decision | The proposal, design or delta spec of the change, same commit as the note |
| An engine fact that stays true | The matching wiki page, before the archive |
| A user-visible change | `CHANGELOG.md`, `Unreleased` |
| Player feedback | `openspec/specs/mod/<feature>/feedback.md` |
| A verified Invasion Mode criterion | `docs/harness/10-invasion-testability/criteria.json` and its README tables |
| A how-the-system-works explanation | The matching wiki page |
