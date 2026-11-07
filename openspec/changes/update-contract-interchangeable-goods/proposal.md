## Why

Issue: #589. The owner asked (2026-11-06) that some goods can stand for each other in a liege contract. Hides and pelts are interchangeable. Berries and mushrooms are interchangeable. A player with mushrooms should be able to pay a request for berries.

## What Changes

- The data file `contracts.json` gets a top level field `groups`: each group is a list of good ids that are interchangeable, with an optional `label` for the card text. More groups can be added later with no code change.
- A request for a good of a group accepts any mix of the goods of the group. The card text shows the label, for example "Deliver 40 berries or mushrooms".
- The "In storage" count and the check of the missing amount add the stocks of all goods of the group.
- Fulfil takes the goods from the group, from the larger stock first.
- One offer never holds two contracts of the same group in one tier. The loader rejects a tier that lists two requests of the same group.
- The starter table keeps one request for berries (id 171) and one for hides (id 3). The request for mushrooms (279) leaves the table, because it is now the same contract as berries. Pelts (id 9) get a name.
- The save format does not change. A saved contract for mushrooms or pelts still loads and counts as its group.

## Impact

- Spec `mod/liege_contracts`: requirements `Contracts live in a data table`, `Requests are deliveries of goods`.
- Code: `mod/InvasionMod/Scripts/features/liege_contracts/` (loader, rules, view, init), `data/liege_contracts/contracts.json`.
- The config weight `liege_contracts.weight[279]` has no effect any more. The weight of a group is the weight of its request (`weight[171]`, `weight[3]`).
