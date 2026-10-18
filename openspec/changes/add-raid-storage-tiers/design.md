# Design: store tiers and the ruin rebuild discount

## Context

Legacy source: `docs/mod/M03-raid_behavior/README.md`, open questions 5 and 6, and tunables "Loss share per trip by store tier" and "Rebuild discount for ruins". The loss share per store, the fire to ruins and the partial rebuild cost were spiked in `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md` and `spike-R8.md`. The manor store is in `docs/harness/12-manor-exploration/implementation-notes/storage-m1.md`.

## Open questions

1. Which building types are guarded and which are open? M00 gives no list. The user decides. Until then the tier list is TBD in the feature config.
2. What are the loss shares per tier? M00 gives no numbers. Values are TBD and tuned in playtests. The spike notes above hold the first numbers; do not copy them here.
3. What is the ruin rebuild discount? M00 says "partial cost" and gives no number. Answer: the user, then a spike on how to set it (Lua write or a pak row).
4. Where does the loss per trip act? The raiders cannot be steered, and the native AI picks the store. Answer: a spike (task 1.1) on whether the mod can remove part of a store between the raid steps without a crash.
