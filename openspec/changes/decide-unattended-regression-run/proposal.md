# Proposal: Decide unattended regression run

Issue: #278. Legacy source: `docs/harness/00-harness-overview/README.md` ("Open decisions") and `docs/harness/08-regression-suite/README.md` (non-goals).

## Why
Spec 00 has two open decisions that nobody closed:
- Should a scheduled task start a nightly regression run? It needs an unlocked desktop session.
- Is a second machine or user account worth it, so the harness does not take over the user's screen?

The suite runner exists (`harness/suite.py`). No schedule uses it.

## What Changes
- The user decides both questions. The decision is written to `design.md`.
- If the answer is yes, the implementation adds a scheduled run and a requirement for it. If no, the change is archived with the decision.

## Non-goals
- A cloud runner or CI for the game (the game is Windows, local, single-player).
- Parallel slots (see `spike-parallel-suite-speedup`).

## Legacy folders
`docs/harness/00-harness-overview/` and `docs/harness/08-regression-suite/` (read only).

## Capabilities
### New Capabilities
None now.

### Modified Capabilities
None now. A "yes" adds a requirement to `harness/regression-suite`.

## Impact
No code until the user decides.
