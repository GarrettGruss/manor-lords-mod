# M06 iteration 01: notes

- Crash: `HarnessSack.sack_goods` on the day-205 save (24 buildings) crashed the game (access violation, run `20261018-050233-020f`, also `20261018-050025-734b` showed the same before the step logs). It re-reads the inventories after each consumed unit. The mod now reads the stores once (`raid_behavior/world.stores`) and only calls `consumeGoodNoCheck`. People and buildings still use `HarnessSack` and worked.
- The region stock can hold more than the stores: a sack reaches only the goods in buildings. The share is planned from the stock. In run `20261018-050851-dab6` one good (228) lost 5 of 11 planned. The scenario checks "at most" per good and 60 to 105 percent of the share for the total stock.
- Lost battle rule (TBD): a role raid that starts to leave for reason `loot` or `time`. Config `sack.lost_reasons`.
- Fatal sack removes all families. Not run in the real game (it would end the run). The fake tests cover the counter.
- Sack does not depend on raid size class yet (TBD).
