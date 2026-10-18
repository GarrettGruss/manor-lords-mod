# Proposal: adopt OpenSpec

Issue: #251. Branch: `feat/adopt-openspec`.

## Why

The repo has 33 harness specs (`docs/harness/`) and 15 mod specs (`docs/mod/`). Each spec README mixes the current state, a dated status log and the plan. Notes pile up in one flat folder per spec (spec 10 has 33 notes). Facts for one feature are spread over several specs. A reader cannot see quickly what is true now and what is history.

OpenSpec separates these jobs. `openspec/specs/` holds the current behavior. `openspec/changes/` holds work in progress. `openspec/changes/archive/` keeps done changes with their full context. The wiki (`docs/wiki/`) keeps the knowledge of how the code and the engine work.

## What Changes

- Add OpenSpec to the repo: `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/`, the `openspec-*` skills and the `/opsx:*` commands for Claude Code.
- New work starts as an OpenSpec change: a harness feature, a mod feature, a mod iteration or a spike.
- Capabilities have three groups: `harness/<name>`, `mod/<feature>` and `process/<name>`.
- A living spec for a capability is made when the first change touches that capability. It is seeded from the "current state" of the legacy README.
- Spike findings go into `notes/` inside the change. At archive time, engine facts that stay true move into the wiki.
- A change is archived in its own pull request, as the last commit before the merge.
- **BREAKING (process):** new branch names `feat/<change-name>` and new issue titles `Change: <change-name>`. The `<NN>` and `M<NN>` numbers stop for new work.
- `docs/harness/` and `docs/mod/` become read-only legacy. Work that is already open there may finish there.
- Update CLAUDE.md, the harness skills, the wiki page `docs-and-specs.md` and `CHANGELOG.md`.

## Non-goals

- No bulk conversion of the 48 legacy specs. Specs grow from real changes.
- No move or rename of legacy folders. Code docstrings, skills, issues and the changelog link to them.
- No custom OpenSpec schema now. The default `spec-driven` schema is used. The `notes/` folder is a project rule, not an artifact.
- No change to `design/`. The user owns the design.
- No change to harness code or mod code.

## Legacy folders

This change replaces the process rules in CLAUDE.md ("Specs and notes", "Git", "GitHub issues") and in `design/mod/README.md`. It does not continue one legacy spec.

## Capabilities

### New Capabilities
- `process/spec-workflow`: how specs, changes, notes, the archive, branches and issues work in this repo.

### Modified Capabilities
- None.

## Impact

- New: `openspec/`, `.claude/commands/opsx/`, `.claude/skills/openspec-*/`.
- Changed docs: `CLAUDE.md`, `docs/harness/README.md` (new), `design/mod/README.md`, `docs/wiki/operations/docs-and-specs.md`, `CHANGELOG.md`.
- Changed skills: `harness-overview`, `harness-git-workflow`, `harness-game-spike`, `harness-dispatch-agents`, `harness-coverage`, `repo-wiki`.
- New tool dependency: the OpenSpec CLI (`@fission-ai/openspec`, Node 20.19 or later). It is needed only to validate and archive changes. Tests and the harness do not need it.
