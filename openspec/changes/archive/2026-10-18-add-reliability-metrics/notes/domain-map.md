# Domain map for this repository

Checked 2026-10-18 (task 1.3).

- `unmapped` churn share: 0.09 (limit `thresholds.unmapped_churn` 0.15).
- Ignored: docs, `CHANGELOG.md`, `openspec/changes/**` (delta specs inside changes are mapped first, by rule order), other skills, spike tools (`harness/tools/s<NN>_*`, `spike*`), probe test scenarios, binary assets.
- The rule `harness/tests/test_fakegame_{name}.py` → `mod/{name}` also matched harness tests (`test_fakegame_harnessbuild.py`). It created 30 domains with no capability. Fix: a generic rule option `require_capability`. A captured domain with no capability folder falls through to the next rule.
- Unknown domain left: `mod/example`. It is a real feature folder with no living spec.
- Limit: every test scenario in `harness/scenarios/` maps to `harness/run-launcher`. A file does not say which harness capability it tests. A finer map needs one rule per file; not done now.
- The living spec `process/reliability-assessment` exists only after the archive. Before it, the check of `capabilities_dir` stops on the rule for the skill folder; the first reports ran with that one rule removed.
