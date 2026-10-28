# Spike C: the march of a spawned army

Spike C was planned only if A failed. A failed. C became: how does an army that spawns at the border get to the target?

## Hostile armies (raids, waves, final army)

No march order is needed. An AI lord army with a challenge (`battlefield_anchor` at the manor) walks to the battlefield on its own. This is the mechanism the Hussite raid already used (change M03 iteration 02). Spawned at the border, the armies walked in: spike B (runs `20261028-020728-5a13`, `20261028-025114-297a`) and a great raid wave with the final army (run `20261028-031402-5569`).

## The relief army (player side): not possible with the known calls

- A player squad does not move without a player order. No Lua call that moves a player squad is known (wiki `engine-limits.md`: spikes `spike-squad-raid-skill` and `spike-raid-skill-near-enemy`).
- Tried instead: the relief army as the army of a second AI lord that is at war with the raid lord (`probe-border-ally`, `probe_border_ally.py`).
  - Run `20261028-021440-80f4`: the ally war and the ally challenge. The second challenge call was refused (the first anchor was still active). The ally squads stopped about 60000 units north of the manor. The game crashed (EXCEPTION_ACCESS_VIOLATION reading 0x00000001e3010360) after about 180 game seconds.
  - Run `20261028-021742-8a3b`: the same with a pause before the second call. The ally challenge failed ("the target has no current region": the target was a lord). The ally squads walked toward the manor without a challenge. The game crashed again with the same address after 120 to 180 game seconds.
  - Run `20261028-022053-6c18`: no war between the lords. All squads of both lords were gone from the list after 20 game seconds (empty army lists). No result.
- Verdict: no safe way was found to bring a friendly army in from the border. A war between two AI lords crashed the game twice with the same address. The call is added to `DANGEROUS_ACTIONS.md`.
- Decision for this change: the relief army stays as it was (`relief_offset`, next to the manor). The owner decides what to do next (proposal, open question 5).

Not verified: other ways to give the relief army a march (a skill or an order on the squad component, or a vassal lord that the game itself calls for help).
