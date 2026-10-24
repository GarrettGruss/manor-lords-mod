# Delivery to the manor store (task 1.3)

The manor store is mod-defined (`HarnessManor`): goods are in the building inventory of a built manor module, up to
`HarnessManor.CAPACITY` units for all goods together (200, raised by the tech tree).
- A new game has no manor (run 20261023-223641-7105: `manor_state` has 0 modules). The delivery needs a built manor module.
- Call: `module:addToInventory({ Type = id, amt = amount })` (proven by the test scenario `manor-storage`).
- Decision (proposal default, no pile fallback): the delivery fails when the village has no built manor or the module cannot hold 60 more
  units. A failed delivery costs nothing and the button text says why ("build a manor first", "manor store full").
- A partial delivery is rolled back with `consumeGoodNoCheck`, so silver is taken only after both goods arrived.
