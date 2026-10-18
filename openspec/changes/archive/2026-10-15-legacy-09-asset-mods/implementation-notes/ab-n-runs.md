# A/B suite with N runs per side (2026-10-13, issue #53)

Suite `harness/suites/pak-ab.json`, scenario `pak-item-value` (hidden; it records the Value of item 17 as a metric).
Variants: `vanilla` and `itemvalue17-pak` (the pak from the pak spike). 5 runs per side, interleaved. Run folder: `runs/suite-20261013-113745-65e3` (not in git).

| Variant | Runs | Passes | Median item17_value |
|---|---|---|---|
| vanilla | 5 | 5 | 0.5 |
| itemvalue17-pak | 5 | 5 | 0.75 |

Verdict: different (Cohen d 99, permutation p 0.008, ranges do not overlap). The expectation "higher by 30%" was met. Run time 450 s for 10 runs.
The values have no spread, so d is very large. The pak was removed after each run (`pakmod.py list`: no pak).
