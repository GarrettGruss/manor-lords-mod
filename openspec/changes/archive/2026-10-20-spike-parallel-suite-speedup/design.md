# Design: Spike parallel suite speedup

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Is a 3 slot suite clearly faster than a 1 slot suite with the same verdicts? | A spike | Task 1.1 to 1.3 |
| Does an `EXCLUSIVE` scenario never overlap another game in a real suite? | A spike | Task 2.1 |
| Bridge timeout under 3 games: raise the 15 s timeout, retry the run, or accept `harness_error`? | The user, after the spike shows how often it happens | Answered 2026-10-20 (owner): keep 15 s and accept a rare `harness_error`; 0 bridge timeouts in 15 parallel runs. Revisit if timeouts appear. |
| Do two games fight for focus or audio, and does a second instance hit a mutex? (legacy "Risks and open questions") | A spike | Task 2.2. The runs in the legacy notes did not show it. |

## Related bug issues (not converted)
- #160: `suite.py` has no `--slot` option. The code now has `--slots N|all` (`harness/suite.py`). The issue may be closed. A review must check this.
- #158: the 5 tests in `harness/tests/test_install_scripts.py` fail while any game runs. Not a legacy plan item.

## Decisions
- Bridge timeout (owner, 2026-10-20): keep 15 s and accept a rare `harness_error`. The spike saw 0 bridge timeouts in 15 parallel runs.
- Slots folder (owner, 2026-10-20): `gameslots.SLOTS_DIR` is the main checkout's `slots` folder (`shared.SHARED_ROOT / "slots"`), as `harness/install.ps1` builds it, so `--slots N` works from any worktree.
