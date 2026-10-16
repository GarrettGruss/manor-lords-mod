# M00 feasibility: bandits and refugees (2026-10-15)

Scope: bandits from low approval, low regional wealth and unhoused refugees. Fighting bandits. Coin buy-back. Refugee waves from a lost vassal. Refugees lower approval and eat food. Housing refugees. Unhoused refugees become bandits. Fear and hope (approval effects). Open questions 7, 14, 15. Balance targets for bandits and refugees.

Method: read only. Evidence is from the spec notes in `docs/harness/` and the mods in `mod/`. No game run. No Python run.

Rating key:
- PROVEN: a note shows it in the real game.
- LIKELY: the needed calls or data exist, but they were not combined in the real game.
- UNKNOWN: needs a spike.
- BLOCKED: notes show it is not possible from Lua or pak.

Game version in all notes: 0.8.111.

## Feasibility table

| Mechanic | Rating | Evidence | Approach | Main risk |
| --- | --- | --- | --- | --- |
| Bandits from low approval | LIKELY | `Region.Approval` reads fine (`mod/RefugeeWaves/Scripts/main.lua` line 75). Approval fell to 47 to 54 in real runs (`docs/harness/15-bandit-settlement/implementation-notes/refugee-followups.md`, item 4; `immigration-surge.md`). No native rule turns low approval into bandits (`homeless-rebellion.md`, Q-R1). | Lua. Read approval each check. Below a line, `family_eject` makes families homeless (they stay in the village). Later, `rebel_raid_rally` sends a raid. | The game recalculates Approval in 1 to 3 game days. Writes do not hold (`docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`, lines 133 to 135). The trigger reads a moving value. |
| Bandits from low regional wealth | UNKNOWN | `Region.regionalWealth` is the game's own property. The HUD shows it as the coins icon (`docs/harness/02-save-autoload/implementation-notes/in-game-messages-and-hud.md`, line 24). It reads, writes and holds (`actions-catalog.md`, lines 127 to 135: 200 stayed 200 after 3 game days). No note links wealth to bandits. | Lua, same path as approval, once a rule is chosen. | No evidence that the game moves wealth by itself. The threshold and the rate are not known. |
| Bandits from unhoused refugees (the raid) | LIKELY | A timer raid from homeless wave families ran in a real game: 2, 3 and 2 families left, then 36 bandit units came (`docs/harness/15-bandit-settlement/implementation-notes/refugee-waves-mod.md`, phase 2). The native game kept homeless families for 20 game days with no rebellion (`refugee-followups.md`, item 1). | Lua. `RefugeeWaves` timer, then `ManorCore.rebel_raid_rally`. | The families are killed, not turned into bandits. `rebel_raid_rally` removes them with `sack_people` (`mod/shared/ManorCore/ManorCore.lua`, line 426 on; `homeless-refugees.md`). The same-people conversion is not safe: `turnToBandit` on a family member crashed the game once (`homeless-rebellion.md`, Crash, 0x1f0). |
| Fighting bandits | PROVEN | Two squads walk to each other and fight with no order, player squads included (`docs/harness/10-invasion-testability/implementation-notes/spike-C1.md`, line 8). Veterancy rises in fights (`spike-C2.md`). A bandit raid attacked the village and burned 1 to 6 buildings (`homeless-rebellion.md`, Part 4). | Native game. The mod only spawns the squads or starts the raid. | A player squad can be moved only with one real OS right click (`docs/harness/10-invasion-testability/implementation-notes/unit-steering.md`). AI and bandit squads cannot be moved from Lua. No scripted "hold this point" order. Fights are a coin toss; use a clear size margin (`spike-C2.md`, line 23). |
| Paying coin to bring bandits back | PROVEN (with conditions) | Letter `raider_suggestSettle+<amount>` sent with `PawnCPP:sendLetter`. Silver fell by the amount. 18 units were removed in 4 to 16 s (`docs/harness/15-bandit-settlement/implementation-notes/bandit-settlement.md`, Q1 and Q3). Families came only into free home slots, one per free slot (`refugee-followups.md`, item 4; `bandit-settlement.md`, "Vacant slots"). With no free slot: 0 families. | Lua: `bandit_letter`, `bandit_tag`, `bandit_state` (`mod/shared/HarnessBandits/HarnessBandits.lua`). | (a) The paragraph needs the tag `attacking`. The harness set it by hand. It is not shown that a natural raid sets it. (b) The game does not check the price. The mod sets it, and any amount was accepted. (c) Nothing happens while the game is paused. |
| Refugee waves from a lost vassal | LIKELY | `settleRegion` on the player region adds 5 families and one homeless tent per call (`docs/harness/15-bandit-settlement/implementation-notes/immigration-surge.md`). The wave mod passed 3 of 3 real runs (`refugee-waves-mod.md`). | Lua: `ManorCore.settle_region`, then `RefugeeWaves`. | Size comes in steps of 5 families per call. Two calls were tested in a row, the third was not (`refugee-followups.md`, "Not answered"). The vassal loss event itself is outside this review. |
| Refugees lower approval | PROVEN | 3 homeless families: approval 71 to 59 in 5 game days (`docs/harness/15-bandit-settlement/implementation-notes/homeless-refugees.md`). 5 homeless: 57. 8 homeless: 52 to 54 (`refugee-followups.md`, item 1). Approval rose 55 to 66 as families were housed (`refugee-cycle.md`). | Native game. The mod adds no penalty. | The drop is a one-time step per count of homeless families (about 2 to 3 points each). It is not a rate. |
| Refugees eat food | PROVEN (qualitative) | After 10 new families (1 member each) food fell to 1 and approval to 47 (`refugee-followups.md`, item 4). Food fell 3 to 2 after a wave (item 1). | Native game. | No food-per-family number was measured. The size of the food loss is unknown. |
| Housing refugees | PROVEN | 5 burgage plots placed by Lua with no mouse. Each plot housed a homeless family when it was built. Homeless 5 to 0 in 12 game days (`refugee-cycle.md`, step 5). `accommodate_homeless` rehoused 3 families at once when slots existed (`homeless-refugees.md`, lead 1). | Lua for the plots (`plot_field_place`, commit). Native game for the move-in. | The plot commit accepts bad spots: no road check, plots on top of houses, plots in the woods were all accepted (`refugee-followups.md`, item 7). The mod must pick good spots. |
| Fear and hope (approval effects) | UNKNOWN | Approval and its factors are readable (`mod/shared/HarnessPolicies/HarnessPolicies.lua`, lines 97 to 131). Policies: `enactPolicy` returns false, `setPolicySigned` works (`docs/harness/16-policy-edicts/README.md`). Strict fasting (lowers approval) showed no measurable effect in the base village (`docs/harness/16-policy-edicts/implementation-notes/policy-followups.md`). Raid dread lowers approval only in the stand-in mod (`docs/harness/10-invasion-testability/criteria.json`, P2). | Lua for reads. A real lever is not known: a signed policy, or a pak data change. | No note writes an approval factor. No real-game test of dread or of a church or wall bonus. Approval is recalculated by the game in 1 to 3 days. |

## Open questions

- Q7 (how order is measured): The game has two readable numbers: `Region.Approval` (the thumbs icon) and `Region.publicOrder` (the scales icon). Both show in the HUD (`in-game-messages-and-hud.md`, lines 22 to 23). `publicOrder` moved on its own (100 to 90, `actions-catalog.md`, line 133). Reads are PROVEN. The single "order" score is a design choice for the user.
- Q14 (what is regional wealth): It is the game's own value, `Region.regionalWealth`. It is shown as the coins icon. The mod can read it, write it and add to it. It holds. Open: whether the game changes it by its own rules (not known).
- Q15 (where refugees wait): A real world building. It is the homeless tent (building type 87). `settleRegion` makes it. Families in it are homeless. The game moves them into free homes (`immigration-surge.md`; `refugee-followups.md`, items 2 and 5). This is PROVEN.

## Balance targets (bandits and refugees)

| Target | Verdict | Note |
| --- | --- | --- |
| Approval under 30% turns 1 to 3 families per month into bandits | UNKNOWN | Approval fell to 47 to 54 in tests, never to 30. The approval floor path (`RefugeeWaves`, 40) was never run in the real game. |
| Regional wealth under a threshold turns 1 to 2 families per month into bandits | UNKNOWN | No threshold found. The game's own wealth rule is not known. |
| A lost vassal sends 30 to 60% of its population as refugees | UNKNOWN | `settleRegion` gives 5 families per call. A share of another region's population is not tested. |
| Unhoused refugees become bandits after 1 to 2 game months | LIKELY | The timer is set in game days (`RefugeeWaves` default 30 days). A 3-day timer ran in the real game. The 30-day timer did not run. The month length in days was not checked in the notes. |
| An armored militia beats a bandit group 1.5 to 2 times its size | UNKNOWN | The N-run method exists (spike C1: loss rates by template). Armor was not tested. |

## Top 3 risks

1. **Crashes from family changes.** `Region:AddNewFamily` crashed the game twice (0x3c1). `SMUnit:turnToBandit` on a family member crashed once (0x1f0). Any design that makes the same people bandits, or creates new families from members, has a crash risk. Use `family_eject` (makes homeless), `settleRegion` (new families) and `sack_people` plus a raid (the families leave). See `refugee-followups.md` item 6 and `homeless-rebellion.md`.
2. **No direct lever for approval.** The game recalculates Approval in 1 to 3 days. Writes do not hold. No approval factor write was tested. The fear and hope effects have no proven real-game lever. The triggers for bandits from low approval or low wealth read values that move on their own.
3. **Coin buy-back depends on a tag and a free slot.** The letter needs the tag `attacking`, which the harness set by hand. It is not shown that natural raids set it. Families come only into free home slots. The price is set by the mod, not the game. Also, raids started by `rebel_raid_rally` ignore their target and walk to the AI waypoint (`homeless-rebellion.md`, Part 4). A chosen rally point is not possible.

## Spikes needed

1. **Natural raid tag.** Watch `bandit_state` during a real raid the game starts itself. Check whether `attacking` is set without `bandit_tag`. Needed for the coin buy-back.
2. **Approval threshold.** Make the village homeless (no free slots) until approval is under 40, then under 30. Watch the bandit side (`units_census`). Check whether the game makes bandits by itself. Tests the 30% target.
3. **Approval lever.** Test a signed policy with an approval factor, and a read of `summedApprovalFactors` over game days with a raid threat. Needed for fear and hope.
4. **Wealth rule.** Read `regionalWealth` over 30 game days in a real game. Set it low with `set_region_value` and watch for any bandit spawn. Answers the wealth row.
5. **Long homeless timer.** Run the homeless timer at its real default (30 game days) and read the month length. Answers the 1 to 2 month target.
6. **Coin price.** Find what the game charges for `settleCost` and whether a refusal rule exists. Needed for a fair buy-back price.
