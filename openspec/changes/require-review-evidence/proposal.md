# Proposal: require review and evidence

Issue: #264. Branch: `feat/require-review-evidence` (stacked on #263).

## Why

The user set these rules on 2026-10-18:
- Spec changes and test results get human review.
- A pull request is in its final state when it is submitted for review.
- The process stays light: pictures and a test overview in the pull request are enough.
- Specs in the changes folder reference their issue.
- Pictures are required as evidence for UI features and models.

One pull request held both the spec and the implementation. So a spec finding came after the code, and two changes (#256, #262) were merged in the GitHub web UI before their archive commit existed.

The user accepted a two-gate model on 2026-10-18:
- **Gate 1:** a spec pull request with only the change folder. The user approves the spec.
- **Gate 2:** an implementation pull request that ends with the archive. The user approves the test evidence.

This matches OpenSpec's own idea of `changes/` (approved, not yet built) and `specs/` (shipped), and it keeps the pull request in its final state at review.

## What Changes

- **BREAKING (process):** two pull requests for a change with something to build.
  - The spec pull request is on `spec/<change-name>`.
  - The implementation pull request is on `feat/<change-name>` and ends with the archive.
  - A change with nothing to build uses one pull request.
- **BREAKING (process):** both gates need the user's approval on GitHub; agents do not merge them. This narrows the advance merge approval of 2026-10-17. Pull requests without a gate (no change folder, no spec change, no test acceptance) may still be merged by an agent after the full tests pass.
- A light pull request body (Summary, Spec changes, Test results table, Evidence, Not verified), and a template in `.github/pull_request_template.md`.
- Picture evidence for visual results:
  - The user's two cases: UI features and models.
  - Five more that the user accepted: materials and textures, building placement and geometry, units in the world, world results the player sees, and text on screen. Text on screen is listed under UI features.
- Evidence in plain git, in `openspec/changes/<change-name>/evidence/`, about 1 MB per change. The user chose plain git over Git LFS.
- Each change names its issue in the proposal, in `x-issue` of `.openspec.yaml` and in a comment in each delta spec. A line above the first section fails `openspec validate --strict`. A comment inside a section passes, and the archive drops it (tested on CLI 1.14.3).
- Update CLAUDE.md, `openspec/config.yaml`, `CONTRIBUTING.md`, the git workflow and scenario skills, the wiki and `CHANGELOG.md`.

## Non-goals

- No Git LFS (it can come later).
- No CI check. The gates are the user's GitHub approvals.
- No change to archived changes.

## Legacy folders

None.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `process/spec-workflow`: two review gates, branches, issue references; new requirements for light pull requests and picture evidence.

## Impact

- Changed: `CLAUDE.md` (specs section, Git merge rules), `openspec/config.yaml`, `CONTRIBUTING.md`, `.claude/skills/harness-git-workflow/SKILL.md`, `.claude/skills/harness-write-scenario/SKILL.md`, `docs/wiki/operations/docs-and-specs.md`, `CHANGELOG.md`.
- New: `.github/pull_request_template.md`.
- This change has nothing to build, so it uses one pull request. It needs the user's approval (gate 1).
