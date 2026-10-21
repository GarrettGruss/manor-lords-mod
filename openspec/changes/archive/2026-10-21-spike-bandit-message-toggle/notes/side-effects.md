# Side effects (task 1.4)

Checked in `s343-b1` (way 4, hide banners) and in the earlier runs.

- Squad behavior: bandit units 36 to 0 after the letter in every run (c1, m1, m2, e1, b1). The hide step changes nothing here.
- Mod buy-back: the same native letter call as `send_settle_letter` was used. Silver was taken (200 to 170) and the units were removed. Families came back in c1, m1, m2 and e1 (10 to 12) and not in b1 (10 to 10). The game brings families back only some of the time (spike S1, 12 of 15), so b1 is no proof of a side effect. The full mod test scenario `bandits-buy-back` was NOT run with suppression (run cap).
- Other letters: after the hide step, the AI-lord letter `welcome_from_hildebolt` still made its own banner "A New Message" in `s343-b1` (`evidence/3-other-letter-still-shows.jpg`). `hidebanners` hides every quest message banner that is live at that moment, so it needs a filter (see recommendation.md). Not tested: whether the player can still open the hidden letter from InBox.
- `markread` changes the flags of bandit letters (no visible effect). `emptybox` deletes letters (it would delete other bandit replies; do not use).
- Crash `s343-d2`: the game crashed (access violation reading 0x60; crash report copied to `runs/s343-d2/crash/`) about 3 s after the settle letter, in a run that only listed the functions of the player and the engine (no hooks). The same flow did not crash in the six later runs (h1, c1, m1, m2, e1, b1). Cause unknown. Treat it as a rare game crash, not as an effect of a suppress way. Run `s343-d1` was a harness error (the `funcs` answer is a list), not a game problem.
- 16 hooks at once (`s343-h1`) did not crash.
- Parallel slots: debug windows of other slots covered the game window in some screenshots (m1, m2, e1). No save call was made. The launcher installed and removed its fixture slot.
