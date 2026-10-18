# M09 iteration 01: notes

## Answers to the README questions
1. How does a wave of N families arrive? Whole `settleRegion` calls on the home region, 5 families each (1 to 3 calls). The wave size is rounded to 5 families.
2. Does the tent slot limit cap the wave? Not seen: 5 families gave 4 homeless in the tent (fixture base, 2 free homes before).
3. Alert: a banner (not checked on screen) and a log line.
4. Food: not measured per family; the game feeds all families.

## Design
- No trigger on a lost vassal yet. M07 iteration 04 calls `refugees.send_wave(families)`; the command `refugees_vassal_lost` is the test path.
- The mod saves the base homeless count and the start day (day + 1) for iteration 02.

## Findings
- New game: home has 5 families and all 5 are homeless at the start (no houses yet), approval stays 50. Waves are meaningful on a settled village (fixture base).
- Approval fell 71 -> 61 in 4 game days with 3 to 4 homeless wave families.
