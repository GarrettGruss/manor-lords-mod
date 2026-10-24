# Implementation notes

- One villager is one family (`getNumHomelessFamilies`, `remove_families`). The leave removes at most 18 families in batches of 6. The village keeps 1 family (the base fixture has 10 families, so 9 leave there). Owner question: should a villager be a person, not a family?
- The game forces speed 1 while new bandits are near, so the test scenario `bandits-banditry-timer` runs its last 10 game days at speed 1.
- The playtest world `playtest-noai` has no bandit pawn: the families leave, `spawned=false`, and the log line `no bandits spawned` is written (run 20261023-233058-18ef).
- On a world with bandits, the game message "Enemy Unit has been spotted" pushes the leave banner out of view. Evidence uses the world without bandits for that picture.
- Test commands added: `bandits_leave_now` (count) and `bandits_set_timer_days_left` (days). `bandits_set_approval` and the roll argument of `bandits_tick_now` are gone. The tech tree `approval_bonus` is ignored.
- Fixture `playtest-noai` is registered in `harness/fixtures/fixtures.json`.
- Run ids (all pass): bandits-banditry-timer 20261023-231116-a0ee (base), 20261023-233058-18ef (playtest-noai); bandits-banditry-banners 20261023-235336-100b (base), 20261023-235609-8d12 (playtest-noai); bandits-order-tick 20261023-234030-6e25; bandits-buy-back, tech-tree-path-choice, invasion-difficulty-pick each pass (20261023-235826-135c, 20261024-000252-7851, 20261024-000106-b3e3).
