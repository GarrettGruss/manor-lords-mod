---
name: reliability-assessment
description: Measure the regression risk of each spec domain from git history and test run results (change failure rate, fix-to-feat ratio, bug lifetime, MTTF, MTTR, flaky rate). Use before a release, when a spec pull request of a feat change is opened, once a month, or when asked about reliability or regression risk.
---

# Reliability assessment

The skill is reusable. Its spec is `spec/README.md`. All values specific to this codebase are in `reliability.json`. The rules for when to assess and what to do with the result are in the living spec `openspec/specs/process/reliability-assessment/spec.md`.

## Run it

```
uv run python .claude/skills/reliability-assessment/scripts/reliability.py assess
```

This writes `docs/reliability/<date>.md` and `.json`, and prints the Markdown. Sub-commands `git` and `runs` print one report only (`--json FILE` saves it). It takes a few seconds.

## Read the result

- **Over a limit** lists the domains that need action. Limits are in `reliability.json` (`thresholds`).
- **CFR** (change failure rate): the share of `feat` commits whose lines a `fix` changed within `cfr.window_days`. High CFR means changes in that domain often break.
- **fix:feat**: fixes per feature. **Bug lifetime**: days from the last edit of the fixed lines to the fix.
- **MTTF / MTTR** (hours): time from a passing test scenario to its next real failure, and from a failure to the next pass.
- **Flaky**: a failure followed by a pass on the same commit. Most runs here are on a dirty tree (`+dirty`), so the flaky count is a low estimate.
- `n=` is the sample count. `low sample` values are not reliable. Read trends, not single values.
- Harness test scenarios in `harness/scenarios/` all map to `harness/run-launcher`. Mod test scenarios map to their feature.

## Act on it

Follow `process/reliability-assessment`:
- A domain over a limit: its next change adds a regression test scenario or only fixes defects.
- `unmapped` churn share over the limit: add patterns to `domains` in `reliability.json`.
- Unknown domains: a captured domain has no capability folder. Add a spec, or a `require_capability` rule.
- Review the fix commit list in the JSON. Many `fix` commits that are not defect repairs mean the labels are noisy: propose a change for defect issues.
- For a `feat` proposal: copy the domain lines into its `Reliability risk` section.

## Change the config

Edit `reliability.json`. Keep the order of `domains`: specific rules first. Then run `assess` and check the `unmapped` share and the unknown domains. Tests: `uv run python -m unittest discover -s .claude/skills/reliability-assessment/tests`.
