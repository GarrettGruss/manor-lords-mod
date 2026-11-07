## Decisions

1. Groups are data: `groups: [{ "goods": [171, 279], "label": "berries/fungi" }]`. A good is in at most one group; a group has at least 2 goods.
2. A request names one good of the group. The contract keeps that good id, so the save format and the weight overrides do not change. The group of a contract is found from its good.
3. The loader fails when two requests of one tier are in the same group (they would be the same contract).
4. Stock is the sum over the group goods. Take order: the good with the larger stock first, then the next. A short take puts every taken unit back (as today).
5. The reward good is never a good of the request group.
6. Card text: `Deliver <n> <label>`; without a label the names are joined with " or ". The card must fit: the real-game screenshot proves it. If "berries/fungi" is too long, the label in the data is shortened.
