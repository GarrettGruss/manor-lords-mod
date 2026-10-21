## 1. Decision

- [-] 1.1 The owner decides question 1 of design.md on the issue. Verified by review of the issue comment. CANCELLED: owner closed the spike as not possible, 2026-10-19.
- [-] 1.2 If the owner folds the spec: copy the verdict into the spec 12 notes folder as the legacy plan says, and close the issue. Verified by review. CANCELLED: owner closed the spike as not possible, 2026-10-19.

## 2. Spikes (only if the owner continues)

- [-] 2.1 Make a fixture with a ring that has no gate (or a very wide opening), then place a normal building inside with the real mouse and count buildings before and after. Verified by a real game run and `notes/gate-free-ring.md`. CANCELLED: owner closed the spike as not possible, 2026-10-19.
- [-] 2.2 Toggle reflected flags that the check might read and repeat the placement. Verified by a real game run and `notes/flag-toggles.md`. CANCELLED: owner closed the spike as not possible, 2026-10-19.
- [-] 2.3 Capture picture evidence (ghost colour and text, placed buildings) with `ctx.screenshot(name)` into `evidence/`. Verified by `evidence/README.md`. CANCELLED: owner closed the spike as not possible, 2026-10-19.

## 3. If a way works

- [-] 3.1 Add a named command with a fake game test in `harness/tests/`. Verified by the test run. CANCELLED: owner closed the spike as not possible, 2026-10-19.
- [-] 3.2 Add a test scenario that covers criterion M2 and passes 3 of 3 real runs. Verified by the run ids. CANCELLED: owner closed the spike as not possible, 2026-10-19.
- [-] 3.3 Write the delta spec and set the issue number. Verified by `openspec validate spike-bailey-buildings --strict`. CANCELLED: owner closed the spike as not possible, 2026-10-19.

## 4. Close

- [x] 4.1 Lasting engine facts moved into the wiki page `docs/wiki/concepts/engine-limits.md`. No user-visible change, so no `CHANGELOG.md` entry.
- [-] 4.2 Fill the test results table of the implementation pull request. Verified by review. CANCELLED: owner closed the spike as not possible, 2026-10-19.
