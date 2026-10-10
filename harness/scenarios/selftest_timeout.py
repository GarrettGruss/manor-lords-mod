"""Test scenario. It sleeps longer than its limit, to test the verdict timeout."""

import time

NAME = "selftest-timeout"
LIMIT_S = 5
HIDDEN = True
SLEEP_S = 40


def run(ctx) -> dict:
    ctx.log.info(f"sleeping {SLEEP_S} s, the limit is {LIMIT_S} s")
    time.sleep(SLEEP_S)
    ctx.log.info("woke up (the launcher should be gone)")
    return ctx.result()
