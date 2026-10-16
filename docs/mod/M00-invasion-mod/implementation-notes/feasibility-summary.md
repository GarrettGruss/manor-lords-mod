# Feasibility summary of the M00 draft (2026-10-15)

Sources: four reviews in this folder (`feasibility-raids.md`, `feasibility-bandits-refugees.md`, `feasibility-vassals.md`, `feasibility-manor-tech-units.md`), written by Haiku agents from the harness notes only. No game run.
The key claims were checked by hand against the notes (see "Checked claims"). Ratings: PROVEN (real game), LIKELY (parts exist), UNKNOWN (spike needed), BLOCKED (notes show no way).

## Verdict
The core of the design is feasible. Most of the "town under pressure" loop rests on things that already worked in the real game.
Five parts of the draft depend on control that the game does not give to Lua. They need a design change or a spike before a feature spec is written (see "Design changes needed").
One cross-cutting gap is not in the draft at all: the mod must keep its own state across a save and a load (see "Mod state across saves").

## What is already proven (building blocks)
- Raids: raid timer write and spawn, raid size in 18-unit squads, countdown banner, sack by share, fire to ruins, partial rebuild cost, goods per store.
- Plunder: the base bandit AI already loots, burns 3 to 7 buildings and leaves with "enough looted". The mod only has to start it.
- Refugees: refugees lower approval (71 to 59 in 5 days), eat food (not measured per family), and can be housed by Lua (5 to 0 homeless in 12 days). The camp is the game's homeless tent (type 87).
- Bandits: the player fights them with the normal squads. Coin buy-back works through the negotiation letter, with conditions (a hand-set "attacking" tag, free home slots, no price check by the game).
- Families to bandits: `homeless_rebel` removes families and bandits appear (spec 15).
- Manor and army: a mod-owned manor store, veterancy, unit stat numbers (`maxSize`), mercenary hire, a garrison limit hook (12 to 36).
- Regions: `regionalWealth` is the game's own value; it reads, writes and holds.

## Likely (parts exist, not combined yet)
- Vassals as AI-lord regions: claim, settle, hand over. But a 2026-10-13 rerun saw no lord build on the base fixture.
- Tribute as silver, wealth or influence payouts (calls verified). Goods transfer between regions: unknown.
- Hussite units from existing foot rows (militia, spear, pole, crossbow). No handgunner row found.
- Army counters (spear against sword measured in an A/B, p 0.029).
- Lost-vassal refugees through `settleRegion` (5 families per call).
- Bandits from low approval, as a mod rule (approval reads fine; the game recalculates it every 1 to 3 days).
- Manor storage upgrade (row write plus an instance copy), plundered start (sacks work at run time; the start state is not tested).

## Design changes needed
| # | Draft item | Finding | Proposed change |
| --- | --- | --- | --- |
| 1 | Bait, decoy storehouse, smarter targeting, raiders going around walls | BLOCKED. Raid targets are ignored, and a move order (`formALineArmy`) is accepted but not obeyed (`15-bandit-settlement/implementation-notes/homeless-rebellion.md`, runs s15-w1, s15-w5). | Drop steering. Difficulty comes from raid size, timing, frequency and spawn side. Raiders use the native target choice. |
| 2 | Laws and vassal policies (conscription, forced labor, trade pacts...) | Game policy effects are native, and `PawnCPP:enactPolicy` returned false in 95 slot and id combinations (`16-policy-edicts`). Policies on regions the player does not own are untested. | Laws and vassal orders become mod-owned settings. Lua applies their effects (silver, approval, tribute rate, levy). They do not use the game's policy system. |
| 3 | Loot drops on death, peasants recover it | UNKNOWN. No ground loot object found; the loot pile is a Lua table only. | Version 1: goods carried by a killed raider go back to the nearest store (abstract). A world pile only if a spike finds an object. |
| 4 | Retreat triggers (morale break, timer end), captain who must die, captain who comes back | UNKNOWN. Morale reads 1.0; no leader unit found. | Spike first. Fallback: the mod ends a raid by a timer or by losses, and removes the survivors. The "captain" becomes the largest squad. |
| 5 | Armor: unarmored units take 2 to 3 times the damage | UNKNOWN. Armor exists as item ids (`armours` in `DT_UnitTemplates`, items in `DT_Items`). No damage or armor value has been read or changed. | Spike: read the armor values in `DT_Items` and A/B one change. Fallback: armor tiers through equipment ids only, and drop the 2 to 3 times target. |

Smaller points:
- Villagers becoming bandits must use `homeless_rebel` (remove families, spawn bandits). `turnToBandit` on a family member is the main suspect of a crash. `Region:AddNewFamily` crashes the game.
- A region claim once triggered the game's victory cinematic (`15-bandit-settlement/implementation-notes/settler-camp.md`). Gaining vassals by claims may end the game. This must be solved before the vassal feature (and it touches the win condition, open question 6).
- Loyalty, the liege, influence spending on aid and finite deposits have no game state. They are mod-owned values.
- Direct orders to AI squads are BLOCKED. Steering through AI inputs (war, influence, silver, challenge) works.

## Mod state across saves (not in the draft)
Many features keep values that the game does not store: the great raid countdown, vassal loyalty, influence balance of the liege, the chosen leadership path, tech nodes, deposit stock, the raid schedule.
Spec 22 rule 4 says a feature keeps no state that the game cannot rebuild after a load. The mod also must never call a save function.
So the mod needs a way to keep its state with each save. Options to test: write the values into game fields that are saved (for example unused counters), or a side file keyed to the save slot and the game date.
This is the largest gap for the design as a whole. It needs a harness spike before the first feature with state.

## Spikes in priority order
1. Mod state across saves (above). Blocks every feature with state.
2. Raid end control: remove a raid's survivors, retreat by timer or losses, a leader unit (SP-R3).
3. Region claim without the victory cinematic, and policies or settings on a non-player region.
4. Armor values in `DT_Items` and one A/B.
5. Ground loot object (SP-R2).
6. Tech tree data: read `DT_RegionDevelopmentTech` and write one node.
7. Retinue size: does the garrison hook change real recruits.
8. Coin buy-back price, approval threshold and the 30-day homeless timer.
Row ids for new rows are already spec 23 (#127).

## Checked claims
- Steering BLOCKED: confirmed in `homeless-rebellion.md` line 140 ("the squad does not obey").
- `enactPolicy` 95 calls: confirmed in `16-policy-edicts/README.md` and `policy-followups.md`.
- Victory cinematic after a claim: confirmed in `settler-camp.md` line 10.
- `turnToBandit` crash: the note says "main suspect", not proven.
- "No armor field": corrected. Armor is item ids; the damage effect is unknown. Rated UNKNOWN, not BLOCKED.
- Not checked by hand: the other PROVEN items. They come from the reviews' citations.

## Side finding
`docs/harness/10-invasion-testability/README.md` says the raid stand-in passed in the real game, but its PENDING section and `raid-standin.md` say the real run is still open. Fix the status line in spec 10.
