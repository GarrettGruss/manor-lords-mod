# Design: Spike parallel suite speedup

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| Is a 3 slot suite clearly faster than a 1 slot suite with the same verdicts? | A spike | Task 1.1 to 1.3 |
| Does an `EXCLUSIVE` scenario never overlap another game in a real suite? | A spike | Task 2.1 |
| Bridge timeout under 3 games: raise the 15 s timeout, retry the run, or accept `harness_error`? | The user, after the spike shows how often it happens | Task 3.1 |
| Do two games fight for focus or audio, and does a second instance hit a mutex? (legacy "Risks and open questions") | A spike | Task 2.2. The runs in the legacy notes did not show it. |

## Related bug issues (not converted)
- #160: `suite.py` has no `--slot` option. The code now has `--slots N|all` (`harness/suite.py`). The issue may be closed. A review must check this.
- #158: the 5 tests in `harness/tests/test_install_scripts.py` fail while any game runs. Not a legacy plan item.
