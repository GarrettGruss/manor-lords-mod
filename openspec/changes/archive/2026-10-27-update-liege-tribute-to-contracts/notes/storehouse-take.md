# Storehouse goods take (task 1.2)

Question: does `consumeGoodNoCheck` on a store make `getStockOfGood` of the region fall by the amount?

Method: test scenario `liege-contracts-complete` (run 20261028-021037-d1a3, default fixture, game build 26185246). It picks `timber_for_the_walls` (60 wood), gives 70 wood with the cheat action `give_item`, and completes the contract. The mod takes the goods in `world.take_goods`: it lists the finished buildings of the player region, keeps the stores of type 6, 72 (tier 1) and 50, 57, 58, 81, 82, 83, 95, 98 (tier 2, as `store_tiers` of `raid_behavior`), sorts tier 1 first and calls `consumeGoodNoCheck` once per unit.

Result: the stock of wood fell from 87 to 27 (metrics `stock_before` 87, `stock_after` 27): exactly 60 units. Silver +100, influence +15, the contract closed, `failed_rewards` 0.

Decision: the take source is the stores of the player region, tier 1 first. No fallback to the manor store is needed. If the take finds fewer units than the stock number says (the stock counts a building that the take list does not know), the units taken are put back, the call is refused, and the message says how many units were found (fake game test `test_a_shortage_at_the_take_refuses_and_changes_nothing_else`).
