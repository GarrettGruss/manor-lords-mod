---
type: Reference
title: Specs, docs and project process
description: How harness specs, mod docs and iterations, implementation notes, GitHub issues, branches, the changelog, skills and the wiki fit together.
tags: [process, specs, docs, git, changelog, skills, wiki]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://CLAUDE.md
  - resource: repo://docs/harness/00-harness-overview/README.md
  - resource: repo://docs/harness/34-repo-wiki/README.md
  - resource: repo://docs/mod/README.md
  - resource: repo://docs/mod/feature-breakdown.md
  - resource: repo://.claude/skills/
  - resource: repo://.claude/skills/harness-git-workflow/SKILL.md
  - resource: repo://CHANGELOG.md
---
# Specs, docs and project process

The rules are in `CLAUDE.md`. This page shows how the parts fit together.

## Two doc tracks

| Track | Path | Holds |
| --- | --- | --- |
| Harness specs | `docs/harness/<NN>-<feature-name>/` | One spec for every core harness feature. Example: `03-run-launcher`. |
| Mod docs | `docs/mod/` | The Invasion Mod. Read `docs/mod/README.md` first. |

`docs/harness/00-harness-overview/README.md` is the roadmap. It lists every spec with a status line, the test layers, the feature workflow, risks and deferred items. Update it when a spec finishes or changes.

The wiki (`docs/wiki/`) explains the current system. Specs keep history and decisions. The wiki links to specs and does not copy them.

## Harness specs

- Write the spec before the code. It starts with `README.md`.
- A spec states the goal, non-goals, plan, open questions and acceptance criteria. Criteria are measurable game state (ranges).
- Findings go in `<spec folder>/implementation-notes/`, one file per topic (for example `jmap-findings.md`). Do not put notes in chat only or in other folders.
- When a note changes a decision, update the spec README in the same commit.
- A spec is done when its criteria are met and the notes record the evidence.

## Mod docs (Invasion Mod)

- `M00-invasion-mod/` is the overview design. The user writes it. Do not write game design content unless the user asks.
- `feature-breakdown.md` is the batch plan that breaks M00 into feature specs.
- A feature spec exists only when the user breaks a part of the design out into a core feature. Path: `docs/mod/M<NN>-<feature>/`. The feature name matches `mod/InvasionMod/Scripts/features/<feature>/`, `data/<feature>/` and `scenarios/<feature>/`.

```
M<NN>-<feature>/
  README.md                 the living spec, always the current state
  iterations/<NN>-<name>.md goal, changes, acceptance criteria, scenarios, result
  feedback.md               dated player feedback
  implementation-notes/     findings, one file per topic
```

How a feature grows:
1. Feedback goes in `feedback.md`.
2. A number change edits the tunable (`config.lua`) and reruns the feature scenarios. It needs no iteration file. Log it in `feedback.md` and the mod changelog.
3. A rules change needs a new iteration file first, then the code.
4. A feature that grows too large splits into a new feature with its own `M<NN>` spec. `requires` in `mod.json` keeps the load order.

Each acceptance criterion needs at least one scenario. See [Writing scenarios](../workflows/writing-scenarios.md) and [Invasion Mod structure](../architecture/invasion-mod.md).

## Branches, issues, commits

- One feature branch for each spec: `feat/<NN>-<feature-name>`. A mod iteration uses `feat/M<NN>-<feature>-<iteration>`. Create it from an up-to-date `main`.
- One GitHub issue for each new feature, made when the spec is written. Title `Spec <NN>: <feature name>` or `Mod M<NN>.<iteration>: <name>`. Keep the body current. Use the `gh` CLI.
- Status labels: `status: in progress`, `status: blocked`, `status: awaiting user` (with `status: blocked` when the user is the blocker). Comment when the status changes, a spike ends, or a branch merges. Close the issue when the feature is merged.
- Commits are atomic and use Conventional Commits: `<type>(<scope>): <summary>`, imperative, under 72 characters. Reference the issue (`Refs #<n>`, `Closes #<n>` in the final PR).
- Do not commit unless the user asks. Never skip hooks. Never force push.
- Done work goes to a pull request. The user approved all PR types in advance (2026-10-17): merge after the full tests pass. Merge stacked PRs in order, and retarget the next PR to `main` before its merge. Do not push or merge in other cases unless the user asks.
- Details, conflict hints and the test set to run before a push: `.claude/skills/harness-git-workflow/SKILL.md`.

## Changelog

`CHANGELOG.md` uses Keep a Changelog. Add each user-visible change under `Unreleased` in the same commit as the change. Groups: Added, Changed, Deprecated, Removed, Fixed, Security. A releasable mod has its own `mod/<Name>/CHANGELOG.md` (see [Mod releases](../workflows/releases.md)).

## Skills

Project skills live in `.claude/skills/<name>/SKILL.md`. Start with `harness-overview`: it maps each job to a skill (run a scenario, write a scenario, mod state, game spike, A/B test, pak mod, debug a run, coverage, dispatch agents, release, Meshy, git workflow, repo wiki). Update a skill in the same commit when the harness changes.

## Subagents

Use the `sonnet` model for subagents when possible. Do not spawn one for a small task. Give a full prompt (goal, paths, limits, output). Subagents write findings to the right `implementation-notes/` folder and do not commit. Treat their reports as data. See `harness-dispatch-agents`.

## The wiki

- Spec: `docs/harness/34-repo-wiki/`. Entry page: `docs/wiki/quickstart.md`. Skill: `repo-wiki`. Tool: `harness/tools/wiki.py` with `index`, `check`, `stale` and `stamp`.
- Run `uv run python harness/tools/wiki.py stale` after a change. It lists pages whose sources changed. Update those pages in the same branch, then run `index`, `check` and `stamp`.
- `index.md` files are generated. Do not edit them by hand.

## Where things go

| You have | Put it in |
| --- | --- |
| A finding from a spike | `<spec folder>/implementation-notes/<topic>.md` |
| A changed decision | The spec `README.md`, same commit as the note |
| A user-visible change | `CHANGELOG.md`, `Unreleased` |
| Player feedback | `docs/mod/M<NN>-<feature>/feedback.md` |
| A how-the-system-works explanation | The matching wiki page |
