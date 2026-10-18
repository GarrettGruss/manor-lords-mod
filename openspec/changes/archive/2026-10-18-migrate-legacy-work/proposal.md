# Proposal: migrate the legacy work

Issue: #269. Branch: `spec/migrate-legacy-work` (stacked on #268).

## Why

The user decided on 2026-10-18 to deprecate the legacy rules and move all legacy work into the OpenSpec change format. Until now, work with an open issue could finish in its legacy folder, and planned work stayed there until it started. That let behavior change without the living specs (spec 34 is the example, fixed by #267).

## What Changes

- **BREAKING (process):** `docs/harness/` and `docs/mod/M<NN>-*/` become read-only history. No work happens there any more. The exception for open legacy work ends. Only the spec 10 coverage data stays live (the coverage tool reads it).
- **Inventory:** every open item of every legacy spec is listed in `notes/inventory-mod.md`, `notes/inventory-harness-1.md` and `notes/inventory-harness-2.md` (151 rows), each with one verdict:
  - CONVERT: the item is now an OpenSpec change;
  - DONE: built on `main`;
  - DROP: obsolete, with the reason;
  - BUG: a bug issue, not a legacy spec;
  - LIVE DATA: the spec 10 coverage data.
- **27 new open changes**, each with a proposal, tasks, a design when there are open questions, delta specs when the behavior is known, and its own issue:
  - Mod: `add-mod-state-region-tags`, `add-raid-carry-caps`, `add-raid-storage-tiers`, `add-liege-influence`, `add-plundered-start`, `decide-open-mod-rules`.
  - Harness, with delta specs: `add-bridge-request-log`, `add-trailer-pipeline`, `move-coverage-criteria-to-openspec`.
  - Harness spikes and decisions (no delta yet): `spike-parallel-suite-speedup`, `spike-other-monitor-and-dpi`, `decide-unattended-regression-run`, `spike-two-year-soak`, `spike-lord-ai-reruns`, `spike-community-mod-leads`, `spike-mcp-client-timeout`, `spike-mod-state-limits`, `spike-new-row-id-persistence`, `extend-mesh-pipeline-checks`, `fix-stale-harness-skill-text`, `spike-blocking-wall-route`, `spike-bailey-buildings`, `spike-composite-building-gaps`, `spike-wagenburg-bandit-camp`, `spike-weaver-extension-shipping`, `spike-wagenburg-manor-reskin`, `add-menu-stay-open-scenario`.
- **This pull request is gate 1 for all 27 changes:** the user reviews them together. After the merge they are open on `main` as approved work. Each starts its implementation pull request (gate 2) on `feat/<change-name>`.
- **Issues:**
  - Ten open legacy issues were retitled to `Change: <name>` (#52, #53, #68, #102, #104, #133, #151, #229, #230, #233).
  - 17 new issues were made (#270 to #286).
  - #203, #237 and #126 were closed as done.
- **Docs:** CONTRIBUTING.md, the git workflow skill, the two legacy banners and the wiki no longer allow work in legacy folders.

## Non-goals

- No deletion, move or rename of legacy files.
- No code change.
- Issue #258 (game-thread scheduler) is new work outside this migration. Bugs #158, #160 and #260 stay bug issues.

## Legacy folders

All of `docs/harness/` and `docs/mod/M01` to `M14` (read only). `docs/mod/M00-invasion-mod/` (the design) is not legacy work.

## Capabilities

### New Capabilities
- None in this change. Some converted changes add capabilities (`mod/liege_influence`, `mod/plundered_start`, `harness/trailer-pipeline`).

### Modified Capabilities
- `process/spec-workflow`: legacy folders are history only; open legacy work is an OpenSpec change.

## Impact

- New: 27 change folders, 3 inventories.
- Changed: `CONTRIBUTING.md`, `.claude/skills/harness-git-workflow/SKILL.md`, `docs/harness/README.md`, `docs/mod/README.md`, `docs/wiki/operations/docs-and-specs.md`, `CHANGELOG.md`.
