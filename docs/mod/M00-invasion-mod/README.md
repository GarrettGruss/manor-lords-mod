# M00: Invasion Mod overview design

Status: draft (2026-10-15), updated with the feasibility decisions (see "Feasibility decisions"). Design content comes from two user briefs. The agent merged them. The user owns the decisions.
Feature breakdown: [`../feature-breakdown.md`](../feature-breakdown.md).
Feasibility review: `implementation-notes/feasibility-summary.md`.
Internal name: `InvasionMod`. Player-facing name: to be decided (it lives only in `mod.json` `display_name`).

Sources:
- Brief A: "Manor Lords: Invasion Mode (Design Brief)", 2026-10-10. Raids, threat clock, outposts, non-terminal defeat.
- Brief B: user brief in chat, 2026-10-15. Lieutenant role, vassals, bandits, liege and influence, two leadership paths.
- Rule for conflicts: brief B is newer and wins. Each conflict is listed in "Merge decisions" so the user can reverse it.

## Vision
The setting is late medieval Franconia, in the time of the Hussite Wars (1419 to 1434).
A Hussite army from Bohemia invades the region in waves, on a telegraphed schedule.
They raid, burn, take supplies and demand ransom from towns.
The people are desperate. Some of them turn to banditry to survive.
The player is a lieutenant lord. The player is sworn to a local city power (the liege).
The task is to restore order to the region.
The player builds a stronghold and a town, binds nearby regions as vassals, and holds the line until the empire's great assault.
The player feels pressure from three sides: the invader outside, unrest inside, and duty to the liege above.
A lost battle sacks the town. It does not delete the game.

## Design pillars
1. **Order is the goal.** Every system feeds one question: is the region more ordered or less ordered than before?
2. **Rule through others.** The player controls only the home region directly. Vassals are controlled only through policies and orders.
3. **Scarcity forces expansion.** Home resources are plentiful but finite. Permanent supplies come from vassals.
4. **Dread from knowing.** Raids are announced with a countdown and a size estimate. The great raid on the main town has a visible clock (Frostpunk).
5. **Raids have goals.** Each raid has one objective. A battle can end without total annihilation: units rout on their own (the game's own behavior).
6. **One path of rule.** The player picks oppression or prosperity. The paths are mutually exclusive. The choice changes how every crisis is solved.

## Core loop
Each cycle feeds the next. The aftermath of one raid is the start position for the next one.
1. **Build and grow:** build and upgrade the town and the manor while the threat clock runs.
2. **Keep order:** keep approval and regional wealth up. Low approval or a poor region makes villagers leave and become bandits. Fight bandits, or pay coin to bring them back.
3. **Expand:** vassalize a neighbor, or send settlers to found a vassal region. Set vassal policies and orders. Receive tribute.
4. **Absorb losses:** a lost vassal sends refugees to the home region. House and feed them, or they become bandits.
5. **Prepare:** invest in palisades, militia, retinue and stockpiles. You cannot afford all of them. Spend influence with the liege if needed.
6. **Defend:** protect the vassals and the main town with what you built.
7. **Aftermath:** losses, burned buildings and stolen goods set the next cycle. Vassals you failed to protect lose loyalty.

## Start state
- The player starts with 1 region under direct control.
- Preferred start: a village that was recently plundered (ruins, a small and scared population, low supplies).
  - Feasibility is not known. See Open questions.
  - Fallback: the normal settler start, with a raid story event in the first days.
- The home region has plentiful natural resources, but they are finite. Iron, salt and other exhaustible resources run out.

## Factions
The game has only foot soldiers (technical limit). All factions fight on foot.

- **Hussites (the invader):** a disciplined peasant army from Bohemia.
  - Units (decision 7): units already in the game. Melee: tier I brigands and spearmen, tier II axe and sword infantry, tier III retinue and poleaxe infantry. Ranged: tier I bows, tier II crossbows. Handgunners are out of scope.
  - Historical model: the "beautiful rides" into Franconia, Bavaria and Saxony (1427 to 1433). They burned towns and took ransom.
  - Ransom demand: before a raid, the Hussite captains can demand a payment to spare the town. This is the first tribute term the player meets.
  - Their war wagons (Wagenburg) are left out. The game cannot show them.
- **Bandits:** villagers and refugees who left because of low approval or hunger. They are local, not part of the invader.
- **Seasons:** the main raids come from spring to autumn. Winter rides are rare but possible (the 1429 to 1430 ride came in winter). Winter strains food.

## Vassals
Vassals replace the "outposts" of brief A. A vassal is an AI-run region that the player rules only indirectly.
- **Two ways to gain one:** vassalize a nearby neighbor, or send settlers to found one. A settled region is also a vassal, but it starts under the player's full control.
- **Indirect control:** policies and orders only. The player does not place buildings there. Policies and orders are mod-owned settings that Lua applies (feasibility decision 2).
- **Loyalty** is a mod-owned value (feasibility decision 8).
- **Victory risk:** a region claim once triggered the game's victory cinematic. Harness spike 26 checks how the game sets the start and victory conditions and whether Lua can change them (feasibility decision 6).
- **Tribute:** vassals send supplies. They are the permanent source of iron, salt and other finite goods.
- **Protection duty:** vassals expect protection from the empire and from bandits.
- **First targets:** the empire raids vassals first, to subjugate or destroy them. More vassals give more tribute but split the player's forces.
- **Loss:** a lost vassal cuts tribute and sends a wave of refugees to the home region (see Refugees).
- **Neglect:** an unprotected vassal may submit and pay tribute to the invader.
- **No intel in version 1:** vassals do not scout and do not leak information. See Out of scope.
- **Fallback:** a fortified vassal can become the fallback capital (see Non-terminal defeat).

## Liege and influence
- The player is sworn to a local city power.
- **Influence** is the resource of the liege relation.
- Gain influence: send tribute to the liege.
- Spend influence: call for military aid, or request villagers, weapons or tools.

## Raids
There are only two raid types (technical limit, user decision 2026-10-15):
- **Plunder** is the minor raid. Raiders loot, kill and burn.
- **Subjugation** is the major raid. An army tries to take a region.

Targets over the game:
- Early raids hit vassals first.
- Plunder raids hit the main town during the whole game.
- A countdown runs to the great raid. The great raid is a subjugation raid on the main town. Its goal is to destroy the town.
- Bandits use the plunder type too, with smaller and weaker groups.

Every raid spawns with one objective. The numbers are starting values to tune. They are not tested balance.
Raiders pick their own targets (the game's AI). The mod does not steer them (feasibility decision 1).

| Raid type | Size | Faction | Composition | Objective | Carry cap per raider | Retreat |
| --- | --- | --- | --- | --- | --- | --- |
| Plunder | Minor | Hussite | Sword men, light spearmen, crossbows | Loot stores, kill villagers, burn buildings | About 10 grain or 5 iron | Native: the base AI leaves when it has looted enough; units rout on their own |
| Plunder | Minor | Bandits | Poorly armed peasants | Food stores, lone workers | About 5 grain | Native |
| Subjugation | Major | Hussite | Mid-size army | A vassal region | None | Vassal submits, or native rout |
| Subjugation (great raid) | Major | Hussite field army | Full army | Destroy the main town | None | Native rout |

Raid behaviors:
- **Loot goes back to the store:** when a looter is killed, the goods it carried go back to the nearest storehouse (feasibility decision 3). No ground pile.
- **Storage tiers:** a guarded granary loses less per trip than an open barn. The manor is the safest store. Its capacity grows through the manor tech tree.
- **Damage:** burned buildings become ruins. Ruins rebuild at partial cost.
- **Rout:** units rout on their own. A mod "mass rout" (end a raid by losses or a timer) is added only if playtests show the game is too punishing (feasibility decision 4).

## Bandits
Villagers become bandits for three reasons:
1. **Low approval:** approval below a threshold.
2. **Low Public Order:** replaces the "low regional wealth" cause (decision 6). Public Order below 75%, 50% and 25% gives a rising chance per season. The user can reverse this.
3. **Unhoused refugees:** refugees with no home turn to banditry (see Refugees).

- The change uses the proven `homeless_rebel` route: the mod removes the families and bandits appear at their homes (feasibility decision 7). No `turnToBandit` and no `Region:AddNewFamily` (crash risks).
- Bandits raid the home region and the vassals, like small local raids.
- The player can fight them, or reason with them and pay coin to bring them back to the village.

## Refugees
- A lost vassal sends a wave of refugees to the home region. The wave size depends on the vassal's population.
- Refugees lower approval while they stay in the region.
- Refugees eat food from the home stores.
- The player must house them. Housed refugees become villagers: workers and mouths.
- Refugees with no home after a set time become bandits.
- This makes each lost vassal a crisis at home, not only a loss of tribute.

## Non-terminal defeat
Losing the main battle triggers a sack, not deletion. The town loses a share of buildings, stockpiles and people, and the game continues.
Repeated sacks inside a short window can still end the game.

Version 1 (scripted events):
- **Sack instead of deletion:** percentage loss of buildings, stockpiles and population.
- **Vassal fallback:** before or during a battle, pay to move families, grain and the best units to a fortified vassal. It becomes the fallback capital.
- **Tribute terms:** the invader offers terms: a one-time payment, or vassalage with yearly tribute. Hostages are dropped (decision 8).

Later layers:
- **Manor holds:** if the town falls but the manor stronghold holds, raiders loot and leave when supplies or morale run out.
- **Occupation:** the invader holds the town for N months and takes a share of production. The player liberates it by revolt or with the liege's relief army.

## Manor and leadership paths
- The manor is the stronghold. The player upgrades it through builds and the tech tree.
- Shared manor upgrades (both paths can take them):
  - **Manor storage:** more storage capacity in the manor. Goods in the manor are the hardest for raiders to reach.
  - **Retinue capacity:** a larger retinue.
- The tech tree has two mutually exclusive paths. Each path unlocks abilities and passive bonuses.
- Laws, vassal policies and the tech tree are owned by the mod (feasibility decision 2). Lua applies their effects. A custom UI from a pak (Widget Blueprint, as in harness spec 16) shows them. The game's own policy system is not used (`enactPolicy` returned false in 95 tries).

First ideas. They are examples, not decisions. Some nodes reuse ideas from the three doctrines of brief A (Bulwark, Warband, Pact).

| | Oppression | Prosperity |
| --- | --- | --- |
| Approval | Higher tolerance for low approval. Unrest is crushed by force. | Approval grows faster. Fewer villagers become bandits. |
| Bandits | Cheaper to fight. Captured bandits become forced labor. | Cheaper to bring back with coin. Returned bandits work at once. |
| Vassals | Demand more tribute. Loyalty held by fear. | Trade and shared defense. Loyalty held by benefit. |
| Liege | Influence from military success. | Influence from tribute and wealth. |
| Laws | Conscription, forced labor on walls, scorched earth. | Militia rights, trade pacts, paying off warbands. |
| Defense style | Bulwark and Warband: walls, garrison, veterans. | Pact: buy off, hire against, redirect raids. |

## Pressure systems
- **Fear and hope:** invasion dread lowers approval. Walls, a strong retinue and a church raise it. A failed defense crushes it.
- **War economy:** shift workers to fletchers, smiths and walls while food and trade suffer.
- **Army counters:** pavises and shields against crossbows and handguns. Pikes and a held line against sword men. Archers against light raiders.
- **Veterancy:** surviving units keep experience. Losing the best retinue hurts.
- **Armor matters:** unarmored units take much more damage. This applies to everyone without armor: villagers in militia, bandits, and light raiders.
  - Goal: investment in armor (smiths, armor stock, liege requests) pays off clearly in battle.
  - Effect: armored militia beat larger groups of bandits. Unarmed villagers die fast when raiders reach them.
  - Feasibility: not known yet. A spike looks for every lever that makes unarmored combat more lethal and armored units stronger (feasibility decision 5).

## Feature map
The core features. Each one becomes a feature spec `docs/mod/M<NN>-<feature>/` when it is broken out.

| Feature | Short goal | Depends on | Spec |
| --- | --- | --- | --- |
| invasion | Schedule plunder raids (minor), subjugation raids (major) and the great raid. Show a countdown and a size estimate. | none | [M02](../M02-invasion/) |
| raid behavior | Start the native plunder AI. Loot of a killed raider goes back to the store. Carry caps. Native rout. | invasion | [M03](../M03-raid_behavior/) |
| bandits | Low approval, low regional wealth or no home turns villagers into bandits. Fight them or pay coin to bring them back. | approval, regional wealth | [M04](../M04-bandits/) |
| refugees | A lost vassal sends refugees. They lower approval and eat food. Unhoused refugees become bandits. | vassals, bandits | [M09](../M09-refugees/) |
| vassals | Vassalize a neighbor or found one with settlers. Indirect control through policies and orders. | regions | [M07](../M07-vassals/) |
| tribute | Vassals send supplies. They expect protection. Failed protection lowers loyalty. | vassals, invasion | [M08](../M08-tribute/) |
| liege and influence | Tribute to the liege gives influence. Influence buys aid, villagers, weapons or tools. | tribute | [M11](../M11-liege_influence/) |
| sack and terms | A lost battle sacks the town. Tribute terms, fallback capital. | invasion, vassals | [M06](../M06-sack_and_terms/) |
| manor stronghold | The manor is the stronghold. Upgrade it through builds and the tech tree: manor storage, retinue capacity. | tech tree | [M13](../M13-manor_stronghold/) |
| finite resources | Home deposits of iron, salt and similar run out. Vassals are the permanent source. | vassals | [M10](../M10-finite_resources/) |
| plundered start | Start in a damaged village. | none | [M14](../M14-plundered_start/) |
| tech tree | Two exclusive paths: oppression and prosperity. Laws and vassal policies. Lua effects, custom UI from a pak. | approval, bandits | [M12](../M12-tech_tree/) |
| mod state | Keep the mod's own values (countdown, loyalty, influence, path, tech, deposits, schedule) with each save. | none | [M01](../M01-mod_state/) (harness spike 24, #128) |
| unit balance | Hussite unit roles from existing foot units. Counters. Veterancy. Much higher damage to unarmored units. | none | [M05](../M05-unit_balance/) |

## Build plan
Manor Lords has limited mod support. AI behavior, regions and new law systems are the riskiest parts. Build in this order:
1. **Scripted raid events** with the threat countdown.
0. **Mod state across saves** (harness spike 24 (#128), result: option A, Tags of the player pawn, see `docs/harness/24-mod-save-state/README.md`). Every later step that keeps values needs it.
2. **Plunder:** start the native plunder AI, loot back to the store on death.
3. **Bandits from low approval and low regional wealth,** and the coin buy-back.
4. **Unit and balance tweaks:** Hussite units, counters and veterancy.
5. **Sack and tribute events** in place of deletion.
6. **Vassals and tribute,** then refugees from lost vassals and the fallback capital.
7. **Liege and influence.**
8. **Leadership paths and the tech tree.**
9. **Plundered start,** if the spike shows it is possible.
10. **Occupation and rebellion:** the heaviest layer, last.

## Progression and pacing
- **Early (year 1):** rebuild the town. First bandit groups appear. First minor raids hit the edge of the home region. The great raid countdown starts.
- **Middle (years 2 to 3):** expand to 2 or 3 vassals. Home iron and salt run low. Raids grow and hit vassals. Pick a leadership path. Use the liege for emergencies.
- **Late (year 3 onward):** the empire tries to subjugate or destroy vassals. Minor raids on the main town become frequent. The great raid arrives. The manor must hold.

Difficulty tiers change what raiders want and how smart they are, not only how many come:
- Raid count and size rise per tier.
- Subjugation raids start later and come more often on higher tiers.
- More frequent raids and different spawn sides.
- Higher carry caps.
- Better equipped raiders (if the armor spike finds a lever).
- Smarter targeting, raiders going around walls and a captain are removed (raiders cannot be steered, feasibility decision 1).

## Balance targets
First guesses. The scenarios will check them later as ranges.
- First minor raid: between day 30 and day 90.
- Warning time before a raid: 2 to 8 game weeks.
- Great raid countdown: 3 to 5 game years.
- Home finite deposits: last 2 to 4 game years at normal use.
- A vassal sends tribute worth 10% to 30% of its production.
- Approval below a threshold (for example 30%) turns 1 to 3 families per month into bandits.
- Public Order below 75%, 50% and 25% gives a 10%, 25% and 50% chance per season (decision 6). Replaces the regional wealth target.
- A lost vassal sends 30% to 60% of its population as refugees.
- Unhoused refugees become bandits after 1 to 2 game months.
- A sack takes 20% to 50% of buildings, stockpiles and population.
- An unarmored unit takes 2 to 3 times the damage of the same unit with armor.
- An armored militia group beats a bandit group 1.5 to 2 times its size in most runs.
- One liege aid call costs about 1 to 2 years of normal tribute in influence.

## Out of scope
- Multiplayer.
- Direct building inside vassal regions.
- New 3D models or new animations in the first version.
- Roguelite carryover between games (brief A "later layer"). Not planned for now.
- Raid types other than plunder and subjugation (technical limit, user decision 2026-10-15): no hostage or slave raids, no captives, no separate burn raids, no test skirmishes.
- Intel in version 1 (user decision, 2026-10-15): no scouting by vassals, no raid size or type reveal from scouts, no intel leaks to the invader. The threat countdown stays.

## Feasibility decisions (user, 2026-10-15)
Taken after the review in `implementation-notes/feasibility-summary.md`.
1. **No raider steering.** Bait, the decoy storehouse, smarter targeting and raiders going around walls are dropped. Raiders cannot be steered from Lua.
2. **Laws, vassal policies and the tech tree are mod-owned.** Lua applies the effects. A custom UI comes from a pak.
3. **Loot goes back to the storehouse** when a looter is killed. No ground pile.
4. **Units rout on their own.** This is accepted as the current state. A mod mass rout is added only if the game is too punishing.
5. **Armor spike:** find levers that make unarmored combat more lethal and armored units much stronger (harness spike 25 (#129)).
6. **Victory cinematic:** probably solved by the game start conditions. Spike on how the game sets scenario settings and whether Lua can change them (harness spike 26 (#130)).
7. **Villagers to bandits** through `homeless_rebel`.
8. **Loyalty, the liege, influence spending and finite deposits** are owned by Lua.
9. **Mod state across saves:** spike (harness spike 24 (#128)). Either write into the save, or keep a mod save system next to the save file. The user approved that the harness makes saves (2026-10-15), so save and load can be tested automatically (rules in CLAUDE.md Safety and spec 24).

## Merge decisions
Places where brief B replaced brief A. The user can reverse each one.
1. **Outposts became vassals.** Brief A outposts are AI villages for scouting and trade. Brief B vassals take their place. One system, not two. The scouting part is cut from version 1 (see Out of scope).
2. **Three doctrines became two paths.** Brief A has Bulwark, Warband and Pact. Brief B has oppression and prosperity. The doctrines now feed ideas into the two paths.
3. **Diplomacy with the invader stays only as tribute terms** after a defeat. The main diplomacy is with the liege and the vassals.
4. **Total Conquest became the great raid,** with a fixed countdown, not a difficulty tier only.
5. **Cumans and Norse raiders became Hussites** (user decision, 2026-10-15). The game has only foot soldiers, so all cavalry ideas are removed: horse archers, kiting, cavalry that avoids walls, and cavalry interception in the Warband doctrine.

## Open questions
1. Which mod hooks does the current game build expose for AI, events, regions and new buildings? (Partly answered by the harness specs in `docs/harness/`.)
2. Can the mod start in a plundered village (ruins, damaged buildings)? Part of harness spike 26 (#130) (start conditions). Sacks at run time already work.
3. How are vassal regions shown in the game? As AI lord regions, as player regions with locked building, or as an abstract layer in Lua only?
4. Answered: policies and orders are mod-owned settings; Lua applies them to any region (decision 2). Open: which effects Lua can apply to a region the player does not control.
5. Answered: the base bandit AI already loots, burns and leaves; the mod starts it. Raiders cannot be steered (decision 1). Open: which AI to reuse for subjugation.
6. Answered (decision 1): survive waves until the relief army comes, then fight a very large battle with the liege's reinforcements. Open: how the difficulty is chosen, when the relief army comes, its size.
7. Answered (decision 2): "order" is the native Public Order (`Region.publicOrder`). Approval stays a separate value.
8. A lost vassal sends refugees (decided). What does its land become: an enemy region, a bandit camp, or empty land that can be retaken?
9. Partly answered (decision 9): the liege is off-screen. Only a custom menu represents it. M11 is backlog, TBD.
10. Can the path choice be undone at a high cost, or is it final?
11. How large should a sack be before it feels fair?
12. Is a second invader faction needed for the first release? Candidate: a mercenary free company that can link to the bandits.
13. Answered (decision 7): existing units are used. No handgunners. See "User decisions".
14. Answered: "regional wealth" is the game's own `regionalWealth` (the HUD coins value). It reads, writes and holds. Open: no game link from wealth to bandits; the mod adds that rule.
15. Answered: refugees wait in the game's homeless tent (building type 87), a real building in the world.
16. Can the mod change manor storage capacity and retinue size? Manor storage is likely (row write). Retinue size is unknown. The armor part moved to harness spike 25 (#129).

## User decisions (2026-10-16)
The user gave these decisions. Features apply them in their own READMEs. The user can reverse each one.
1. **Win condition.** During the great raid the player must survive waves of attackers until the relief army arrives. Then the player gets a very large battle. The king or liege sends reinforcements under the player's control. With goals = Endless (spec 26), this win is a mod rule. Affects M02, M06, M07. Answers open question 6.
2. **Order is the native Public Order.** It is the HUD scales icon and the value `Region.publicOrder`. It reads and writes (`docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`, `docs/harness/04-telemetry-and-assertions`). Approval stays a separate game value. Answers open question 7.
3. **Row id blocks confirmed.** Block start is 1000 + 100 times the M number. M02 gets 1200 to 1299, and so on.
4. **Raid info UI.** One custom widget (a pak widget, as in harness spec 16) shows all raid information: countdown, size estimate and more. Applies to M02.
5. **Vassal model.** Still open. It is being explained to the user.
6. **Bandit conversion uses Public Order.** Below 75%: 10% chance. Below 50%: 25%. Below 25%: 50%. Conversion ticks once per season (winter, spring, summer, fall). The values are starting tunables. This replaces the low regional wealth cause. The refugee cause stays (M09). Applies to M04.
7. **No handgunners.** Hussites use units already in the game. Melee: tier I brigands and spearmen, tier II axe and sword infantry, tier III retinue and poleaxe infantry. Ranged: tier I bows, tier II crossbows. Applies to M05 and the M02 raid composition.
8. **No hostages.** Use the game's native sack and loot mechanics. Sack size is proportional to a difficulty indicator, an integer from 1 to 3 for now. Each raid has a base size multiplier: small 1, medium 2, large 3. Unit count is the multiplier times the difficulty. Applies to M02, M03, M06.
9. **The liege is off-screen.** For now only a custom menu represents the liege. M11 is backlog, TBD.
10. **Tech tree node list and M14.** Still open. They are being explained to the user.

Follow-up decisions (user, 2026-10-16, later the same day):
11. **Difficulty is chosen by the player at the start** (1 to 3). Applies to M02.
12. **Great raid for now:** 1 times difficulty waves, and every wave is a large raid. A large army is 15 units. (Open: is a unit one soldier or one squad? See M02.)
13. **Bandit chance is rolled once per region** at each season tick. Applies to M04.
14. **Low approval debuffs Public Order.** Approval does not turn villagers into bandits on its own; it lowers Public Order, and Public Order drives conversion. Oppression techs grant Public Order boons that offset low approval. Prosperity techs boost approval, which removes the Public Order debuff. Applies to M04 and M12.
15. **Sack size grows in a straight line with difficulty for now.** It may become logarithmic. This is decided in playtests. Applies to M06.
16. **A large army is 15 squads.** The count is tuned in playtests. The great raid's final "very large battle" is a reward for surviving, so difficulty does not scale it for now.
17. **The relief army is 15 squads** under the player's control. Changed by decision 26.
18. **Raid size (small, medium, large) is random** for normal raids, for now. The great raid waves are all large.
19. **Public Order debuff from approval:** debuff = (100 - approval) x difficulty, in Public Order points. Base rate 1:1. Example: approval 65 (a normal village) gives Public Order 65 at difficulty 1. Linear steps. Tech boon sizes are TBD.
20. **Vassal model A (answers decision 5).** The player starts with no vassals. The player settles a region, and the game hands it to a friendly AI lord who rules in the player's name. The user does not expect the AI lord to declare war; playtests watch for it.
21. **Tribute is a Lua rule:** at each season tick, the mod adds goods to the player's stock. No goods transfer between regions. Applies to M08.
22. **Tech tree (answers decision 10).** The 4-node draft per path is approved for now (Martial Law, Iron Hand, Veteran Levies, Fear of the Lord; Fair Courts, Amnesty, Militia Rights, Golden Age). Path and node choices are final and exclusive.
23. **Tech tree is data-driven.** It changes often. The feature JSON defines the tree as a linked list of nodes. The mod builds the tree from it. The JSON may hold optional layout data (positions) for the menu. No hard-coded tree, unless a technical limit forces it. Applies to M12.
24. **Tech cost is free for now.** One node slot unlocks each time the settlement level rises. Applies to M12.
25. **M14 plundered start is out of scope for the first release.**
26. **Relief army size scales down with difficulty** (replaces the fixed size of decision 17). The liege sends 15 squads at difficulty 1 and 0 squads at difficulty 3 (the hardest). Difficulty 2: linear in between, 7 or 8 squads (open; tune in playtests). Applies to M02 (great raid end) and M06.
