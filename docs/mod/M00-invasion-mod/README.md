# M00: Invasion Mod overview design

Status: draft (2026-10-15). Design content comes from two user briefs. The agent merged them. The user owns the decisions.
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
5. **Raids have goals.** Each raid has one objective and one breaking point. A battle can end without total annihilation (RimWorld).
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
  - Units: sword men, pikemen and spearmen, crossbowmen, and early handgunners if the game has a fitting unit.
  - Historical model: the "beautiful rides" into Franconia, Bavaria and Saxony (1427 to 1433). They burned towns and took ransom.
  - Ransom demand: before a raid, the Hussite captains can demand a payment to spare the town. This is the first tribute term the player meets.
  - Their war wagons (Wagenburg) are left out. The game cannot show them.
- **Bandits:** villagers and refugees who left because of low approval or hunger. They are local, not part of the invader.
- **Seasons:** the main raids come from spring to autumn. Winter rides are rare but possible (the 1429 to 1430 ride came in winter). Winter strains food.

## Vassals
Vassals replace the "outposts" of brief A. A vassal is an AI-run region that the player rules only indirectly.
- **Two ways to gain one:** vassalize a nearby neighbor, or send settlers to found one. A settled region is also a vassal, but it starts under the player's full control.
- **Indirect control:** policies and orders only. The player does not place buildings there.
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

Every raid spawns with one objective and one breaking point. The numbers are starting values to tune. They are not tested balance.

| Raid type | Size | Faction | Composition | Objective | Carry cap per raider | Retreat trigger |
| --- | --- | --- | --- | --- | --- | --- |
| Plunder | Minor | Hussite | Sword men, light spearmen, crossbows | Loot stores, kill villagers, burn buildings | About 10 grain or 5 iron | Full loot, raid timer ends, or morale break |
| Plunder | Minor | Bandits | Poorly armed peasants | Food stores, lone workers | About 5 grain | Light losses or morale break |
| Subjugation | Major | Hussite | Mid-size army | A vassal region | None | Vassal submits, or morale break |
| Subjugation (great raid) | Major | Hussite field army | Full army with its captain | Destroy the main town | None | Captain dies only |

Raid behaviors:
- **Loot drops on death:** looters run for the map edge. Kill one and the goods drop for peasants to recover.
- **Bait:** raiders go for the nearest high-value stockpile. A decoy storehouse in a killing zone steers them.
- **Storage tiers:** a guarded granary loses less per trip than an open barn. The manor is the safest store. Its capacity grows through the manor tech tree.
- **Damage:** burned buildings become ruins. Ruins rebuild at partial cost.

## Bandits
Villagers become bandits for three reasons:
1. **Low approval:** approval below a threshold.
2. **Low regional wealth:** a poor region pushes peasants to banditry, even when approval is fine.
3. **Unhoused refugees:** refugees with no home turn to banditry (see Refugees).

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
- **Tribute terms:** the invader offers terms: a one-time payment, hostages, or vassalage with yearly tribute.

Later layers:
- **Manor holds:** if the town falls but the manor stronghold holds, raiders loot and leave when supplies or morale run out.
- **Occupation:** the invader holds the town for N months and takes a share of production. The player liberates it by revolt or with the liege's relief army.

## Manor and leadership paths
- The manor is the stronghold. The player upgrades it through builds and the tech tree.
- Shared manor upgrades (both paths can take them):
  - **Manor storage:** more storage capacity in the manor. Goods in the manor are the hardest for raiders to reach.
  - **Retinue capacity:** a larger retinue.
- The tech tree has two mutually exclusive paths. Each path unlocks abilities and passive bonuses.

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

## Feature map
The core features. Each one becomes a feature spec `docs/mod/M<NN>-<feature>/` when it is broken out.

| Feature | Short goal | Depends on | Spec |
| --- | --- | --- | --- |
| invasion | Schedule plunder raids (minor), subjugation raids (major) and the great raid. Show a countdown and a size estimate. | none | not yet |
| raid behavior | Plunder goal states: seek target, loot, kill, burn, flee. Loot drops on death. Carry caps and retreat triggers. | invasion | not yet |
| bandits | Low approval, low regional wealth or no home turns villagers into bandits. Fight them or pay coin to bring them back. | approval, regional wealth | not yet |
| refugees | A lost vassal sends refugees. They lower approval and eat food. Unhoused refugees become bandits. | vassals, bandits | not yet |
| vassals | Vassalize a neighbor or found one with settlers. Indirect control through policies and orders. | regions | not yet |
| tribute | Vassals send supplies. They expect protection. Failed protection lowers loyalty. | vassals, invasion | not yet |
| liege and influence | Tribute to the liege gives influence. Influence buys aid, villagers, weapons or tools. | tribute | not yet |
| sack and terms | A lost battle sacks the town. Tribute terms, fallback capital. | invasion, vassals | not yet |
| manor stronghold | The manor is the stronghold. Upgrade it through builds and the tech tree: manor storage, retinue capacity. | tech tree | not yet |
| finite resources | Home deposits of iron, salt and similar run out. Vassals are the permanent source. | vassals | not yet |
| plundered start | Start in a damaged village. | none | not yet |
| tech tree | Two exclusive paths: oppression and prosperity. | approval, bandits | not yet |
| unit balance | Hussite unit roles from existing foot units. Counters. Veterancy. Much higher damage to unarmored units. | none | not yet |

## Build plan
Manor Lords has limited mod support. AI behavior, regions and new law systems are the riskiest parts. Build in this order:
1. **Scripted raid events** with the threat countdown.
2. **Plunder goal states:** seek target, loot, kill, burn, flee, loot drops on death.
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
- Smarter targeting: raiders go for the best stockpile. Raiders go around walls to find weak points.
- Higher carry caps and lower morale breaks.
- A captain who escapes comes back stronger.
- Top tier: raiders retreat only when the captain dies.

## Balance targets
First guesses. The scenarios will check them later as ranges.
- First minor raid: between day 30 and day 90.
- Warning time before a raid: 2 to 8 game weeks.
- Great raid countdown: 3 to 5 game years.
- Home finite deposits: last 2 to 4 game years at normal use.
- A vassal sends tribute worth 10% to 30% of its production.
- Approval below a threshold (for example 30%) turns 1 to 3 families per month into bandits.
- Regional wealth below a threshold turns 1 to 2 families per month into bandits. The threshold is to be tuned.
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

## Merge decisions
Places where brief B replaced brief A. The user can reverse each one.
1. **Outposts became vassals.** Brief A outposts are AI villages for scouting and trade. Brief B vassals take their place. One system, not two. The scouting part is cut from version 1 (see Out of scope).
2. **Three doctrines became two paths.** Brief A has Bulwark, Warband and Pact. Brief B has oppression and prosperity. The doctrines now feed ideas into the two paths.
3. **Diplomacy with the invader stays only as tribute terms** after a defeat. The main diplomacy is with the liege and the vassals.
4. **Total Conquest became the great raid,** with a fixed countdown, not a difficulty tier only.
5. **Cumans and Norse raiders became Hussites** (user decision, 2026-10-15). The game has only foot soldiers, so all cavalry ideas are removed: horse archers, kiting, cavalry that avoids walls, and cavalry interception in the Warband doctrine.

## Open questions
1. Which mod hooks does the current game build expose for AI, events, regions and new buildings? (Partly answered by the harness specs in `docs/harness/`.)
2. Can the mod start in a plundered village (ruins, damaged buildings)? This needs a spike.
3. How are vassal regions shown in the game? As AI lord regions, as player regions with locked building, or as an abstract layer in Lua only?
4. Can Lua apply policies and orders to a region the player does not control?
5. Can the game spawn raiders that steal and carry goods, not only fight? Which existing AI (bandits, the Baron) can be reused for plunder and for subjugation?
6. What is the win condition: survive the great raid, hold until the liege's relief army comes, defeat the warlord, or reach a set order score?
7. How is "order" measured and shown to the player?
8. A lost vassal sends refugees (decided). What does its land become: an enemy region, a bandit camp, or empty land that can be retaken?9. Is the liege a real entity in the world (troops that arrive), or only a menu with effects?
10. Can the path choice be undone at a high cost, or is it final?
11. How large should a sack be before it feels fair?
12. Is a second invader faction needed for the first release? Candidate: a mercenary free company that can link to the bandits.
13. Which existing foot units can stand in for sword men and handgunners? This needs a check of the unit data.
14. What is "regional wealth" in the game? Is it the game's own region wealth value, or a value the mod computes? This needs a spike.
15. Where do refugees wait before they get a home: a camp entity in the world, or only a counter in Lua?
16. Can the mod change manor storage capacity, retinue size and the armor damage factor? Lua at run time, or a pak data change? This needs a spike.
