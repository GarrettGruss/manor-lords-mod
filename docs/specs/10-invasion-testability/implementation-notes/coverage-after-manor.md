# Coverage after the manor spike (spec 12)

Date: 2026-10-11. Branch `feat/33-manor-spike`. Tool: `harness/tools/coverage.py`.

- M1 (the manor can store goods): method verified. Scenario `manor-storage`, 3 of 3 real runs (`manor-storage-1` to `-3`). The store is mod-defined on the Keep inventory and the harness finishes the Keep by a shortcut (see spec 12 `storage-m1.md`).
- M2 (normal buildings inside the manor area): not verified. See spec 12 `workaround-m2.md`.

Result: 36 of 39 A and P criteria with a verified method (92%, target 90%). Blocked: O1 to O4, R5, S4, S5 (unchanged).
