# Suite choice for `tech-tree-menu-stay-open` (task 1.2, recommendation)

Recommendation: keep it out of `core.json`. Run it on demand, and add a small suite `menu-soak.json` only if the owner wants a repeatable check.

Reasons:
- The scenario takes about 6 minutes (300 s wait, then clicks). `core.json` has a 1800 s budget for fast scenarios.
- It uses real mouse input and is `EXCLUSIVE`. No other game may run at the same time.
- It needs `--pak techmenu`. The existing suites run without a pak, except the `*-ab.json` suites.
- No existing suite holds a real-click scenario (`tech-tree-widget-clicks` is in none). `soak.json` repeats only `smoke`.

If a suite is added: `{"name": "menu-soak", "scenarios": [{"scenario": "tech-tree-menu-stay-open", "repeat": 3}], "time_budget_s": 3000, "flake_retries": 0}`. Check first that `suite.py` can pass `--pak`. Task 1.1 needs 3 of 3 real runs.
