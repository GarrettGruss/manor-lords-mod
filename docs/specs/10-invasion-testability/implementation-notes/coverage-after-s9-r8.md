# Coverage after S9 and R8

Date: 2026-10-10. Tool: `harness/tools/coverage.py` on branch `feat/31-ui-refugees-rebuild`.

- Criteria: 38 (A 35, P 2, H 1). A and P criteria with a verified method: 35 of 37 = 95% (target 90%).
- Verified by this branch: T4 (`ui-countdown`, 3 of 3 real runs) and R8 (`rebuild-cost`, hidden, real mouse, 3 of 3 real runs).
- Still without a verified method (2 of 37): P3 (refugees, see `spike-P3.md`) and Q4 (looks of units, animations and UI: a person judges).
- T4 is mark P: the harness proves the text and the screenshot. How the banner looks stays with Q4.
- The hidden scenario `rebuild-cost` needs the real OS mouse, so it is not in any suite. The tool counts it by its `COVERS` tag.
