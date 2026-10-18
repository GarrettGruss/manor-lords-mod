# Invasion Mod: decision log

The design decisions of the user, in force unless a later decision changes them. Numbers are kept as they were in M00, because specs, changes and code comments cite them (for example "decision 28"). Add new decisions at the end. The user owns this log.
Moved from the M00 overview design on 2026-10-18 (change `split-design-brief`). "Open question N" means the list in the archived M00 document (`openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/README.md`). The open questions that are not answered are in the change `decide-open-mod-rules`.

## Feasibility decisions (user, 2026-10-15)
Taken after the review in `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-summary.md`.
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

## User decisions (2026-10-16)
The user gave these decisions. Features apply them in their own READMEs. The user can reverse each one.
1. **Win condition.** During the great raid the player must survive waves of attackers until the relief army arrives. Then the player gets a very large battle. The king or liege sends reinforcements under the player's control. With goals = Endless (spec 26), this win is a mod rule. Affects M02, M06, M07. Answers open question 6.
2. **Order is the native Public Order.** It is the HUD scales icon and the value `Region.publicOrder`. It reads and writes (`openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md`, `openspec/changes/archive/2026-10-15-legacy-04-telemetry-and-assertions`). Approval stays a separate game value. Answers open question 7.
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
26. **Relief army size scales down with difficulty** (replaces the fixed size of decision 17). The liege sends 15 squads at difficulty 1 and 0 squads at difficulty 3 (the hardest). Difficulty 2: linear in between, 7.5 rounded up to 8 squads (decision 28). Applies to M02 (great raid end) and M06.

Decisions of 2026-10-17:
27. **Loss of the great raid's final battle: TBD.** There is no rule for now. M06 and M02 leave it open.
28. **All difficulty scaling rounds up for now.** Any scaled count or share uses the ceiling. Example: the relief army at difficulty 2 is ceil(7.5) = 8 squads. Decision 26 now says 8, not "7 or 8".
29. **Tech tree boon sizes (TBD, tuned in playtests).** Martial Law: Public Order +10. Iron Hand: Public Order +15 and buy-back cost +25%. Veteran Levies: militia defence +10%. Fear of the Lord: Public Order +25 while the garrison is at least 4 squads. Fair Courts: approval +5. Amnesty: buy-back cost -50%. Militia Rights: militia attack +10%. Golden Age: approval +15. The agent chose the numbers marked "+10%", "+25%" and "4 squads". The user gave the others. Applies to M12.
30. **Raid size values (TBD, values chosen by the agent, tuned in playtests).** The base multipliers stay small 1, medium 2, large 3. Random size class weights: small 50%, medium 35%, large 15%. The class is rolled once per normal raid, with fixed weights all game. Unit count = multiplier x difficulty, in squads, at least 1. Scaled counts round up (decision 28). The great raid waves stay large. Applies to M02, M03, M04, M06.
31. **Raid unit source (user decision 2026-10-18).** Hussite raids use the unit tiers: the role raids of M05.02, spawned with `spawnArmy`, even though they do not leave on their own yet (M03.02 adds the leave rules). Small bandit raids (M04 bandits and any non-Hussite raid) keep the native `spawnRaiders` plunder raid. Applies to M02, M03, M04, M05.
