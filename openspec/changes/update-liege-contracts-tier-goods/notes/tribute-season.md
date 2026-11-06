# Tribute pause (spike 1.3)

No game spike was needed: the tribute feature pays at each game month change (`run_tick`). The pause is a saved counter `tribute_skip_months`. A tick that finds a value above 0 pays nothing and lowers the value by 1. `tribute_season` sets it (3 months is one season). Tested in the fake game (`harness/tests/test_fakegame_liege_contracts.py`). The real game run of `fulfil` checks that the value is set (a real month change needs about 30 game days).
