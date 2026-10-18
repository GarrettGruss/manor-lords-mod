# Proposal: add reliability metrics per spec domain

Issue: #289. No legacy folder.

## Why

The harness and the mod grow fast (189 `feat` and 58 `fix` commits, 515 runs). We do not know which spec domains break most often, or how fast we repair them. Without numbers we cannot judge the risk of a regression before a change. The numbers only help if the process uses them, so this is a process change.

## What Changes

- A reusable skill `.claude/skills/reliability-assessment/` with its own spec, a generic script and tests. It can be copied to other codebases.
- One config file `reliability.json` holds everything specific to a codebase: the domain map, the commit type pattern, the run result format, and every constant (window, sample limits, thresholds).
- The script gives three reports:
  - `git`: feat and fix counts, fix-to-feat ratio, churn, change failure rate, bug lifetime per domain
  - `runs`: MTTF, MTTR and flaky rate per test scenario and domain
  - `assess`: both reports and the domains over a limit
- New process rules (`process/reliability-assessment`): when to assess, and what to do with a domain over a limit.
- Proposals of `feat` changes state the reliability risk of their domains (`process/spec-workflow`).

## Non-goals

- A harness change. The script reads existing run files.
- Defect tracking with GitHub issues. A rule says when to propose it.
- Dashboards or a hosted page.
- Automatic gates that block a merge.
- Exact values. Reports show counts and sample sizes.

## Capabilities

### New Capabilities
- `process/reliability-assessment`: when to assess and how to act on the results.

### Modified Capabilities
- `process/spec-workflow`: a `feat` proposal has a `Reliability risk` section.

## Impact

- Code: only `.claude/skills/reliability-assessment/` (`SKILL.md`, `spec/README.md`, `reliability.json`, `scripts/reliability.py`, `tests/`).
- Reports: `docs/reliability/`.
- Skills: `harness-release` (assessment step), `harness-overview` (names the skill).
- Docs: a wiki page, `CHANGELOG.md`.
