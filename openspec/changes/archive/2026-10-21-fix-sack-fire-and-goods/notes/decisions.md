# Decisions

## 2026-10-21: accept the loss of goods in a fire
- Owner: "accept the loss". A store that burns may lose goods in the fire (spike: 11 to 60 percent, see `store-burn-goods.md`).
- The mod does not delete goods from a sacked building beyond what the fire does. The mod does not move or add back goods.
- Only the plunder mechanic removes goods on purpose.
- This replaces the earlier rule that stores keep all goods (proposal, design and delta spec are updated).

## Earlier: fire needs raiders present
- A sack fire runs with raiders present, because villagers flee from nearby soldiers and do not fight the fire (`fire-during-raid.md`).

## Sack timing (open)
- The sack still runs when the raid begins to leave. In a forced raid the raiders were about 11000 units from the village at that moment (`fire-during-raid.md`, follow-up).
- Kept as is. It is an open question for the owner whether the sack should run later. The default `sack.method` stays `collapse` (rubble at once, no fire to fight) until this is answered.
