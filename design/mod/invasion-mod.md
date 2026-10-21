# Invasion Mod: design

The guiding philosophy of the Invasion Mod. Every mod spec and change serves it. The user owns this document; agents change it only when the user asks.
Split from the M00 overview design on 2026-10-18 (change `split-design-brief`). The decision log is in [`decisions.md`](decisions.md). The full original M00 document (with the old feature map, build plan, balance targets and open questions) and the feasibility reviews of 2026-10-15 are archived in `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/`.

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
7. **Aftermath:** losses, burned buildings and stolen goods set the next cycle.

## Start state
- The player starts with 1 region under direct control.
- Preferred start: a village that was recently plundered (ruins, a small and scared population, low supplies).
  - Feasibility is not known. See the change `add-plundered-start`.
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
- **Victory risk:** a region claim once triggered the game's victory cinematic. Harness spike 26 checks how the game sets the start and victory conditions and whether Lua can change them (feasibility decision 6).
- **Tribute:** vassals send supplies. They are the permanent source of iron, salt and other finite goods.
- **Protection duty:** vassals expect protection from the empire and from bandits.
- **First targets:** the empire raids vassals first, to subjugate or destroy them. More vassals give more tribute but split the player's forces.
- **Loss:** a lost vassal cuts tribute and sends a wave of refugees to the home region (see Refugees).
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
| Subjugation | Major | Hussite | Mid-size army | A vassal region | None | Vassal is lost, or native rout |
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
| Vassals | Demand more tribute. | Trade and shared defense. |
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

## Out of scope
- Multiplayer.
- Direct building inside vassal regions.
- New 3D models or new animations in the first version.
- Roguelite carryover between games (brief A "later layer"). Not planned for now.
- Raid types other than plunder and subjugation (technical limit, user decision 2026-10-15): no hostage or slave raids, no captives, no separate burn raids, no test skirmishes.
- Intel in version 1 (user decision, 2026-10-15): no scouting by vassals, no raid size or type reveal from scouts, no intel leaks to the invader. The threat countdown stays.
