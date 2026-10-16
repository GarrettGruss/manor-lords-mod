# Spec 15: Refugee waves (bandit settlement and homeless refugees)

Scope change (user, 2026-10-12): the spec covers refugee waves. Bandits who settle after a negotiation are one source of a wave.

Spec 13 lead (2026-10-14): MLHomelessTentMod places the game's own tent (row 87) by setting the pawn building id and using the normal preview, see `../13-mod-inspection/implementation-notes/ml-homeless-tent.md`.
The folder keeps its old name (`15-bandit-settlement`) so links in issues, notes and the changelog stay valid.
Feature section: "Feature: refugee waves" below. Open spike questions: #61.

Status: spike done (2026-10-12), reverse-direction spike done (2026-10-12). Negotiation path found and commands added. With vacant home slots the letter `raider_suggestSettle` gave +1 family per squad (2 of 2 tries, control flat); the cheat `SettleRaiders` gave none. See `implementation-notes/bandit-settlement.md`.
Tent spike (2026-10-12): a homeless tent (type 87) has no family slot in its stats. It could not be placed (no mouse-free call known, the real mouse did not reach the game). A mouse-free spot finder exists. See `implementation-notes/tent-placement.md`.
Reverse direction (2026-10-12): families -> bandits. `homeless_rebel` removes families and bandits appear at their homes (idle) or a real raid targets them (attacks, burned 8 buildings). `turnToBandit` on a family member took it out of its family; one run later crashed (cause open). See `implementation-notes/homeless-rebellion.md`.
Part 2 (2026-10-12): the `mode=home` squads are not idle. They attack about 650 game seconds (16 game days) after the spawn. No call made them faster (tag, 0-unit raid, real raid). `MLCheatManager:Rebel` gives the village to the bandit lord. See "Making home squads attack" in `implementation-notes/homeless-rebellion.md`.
Part 3 (2026-10-12): rally in the woods. `forest_spot` finds woods by reading foliage instances. Rebels cannot be held at a chosen point (no move order works, a challenge does not hold them). They rally at the AI waypoint (-31000,-22500, inside the player region) for about 480 game seconds and attack about 650 game seconds after the spawn. The settle letter removes rebels in the rally and in the attack, but gave no family for them (3 tries); a raid squad gave +2. Fallback "spawn, kill, raid" works. See "Rally in the woods" in `implementation-notes/homeless-rebellion.md`.
Part 4 (2026-10-12): raid aimed at the woods. A real raid ignores its target: it appears at the map edge, burns on the way, stands at the AI waypoint for 50 to 100 game seconds, then attacks (about 360 to 430 game seconds after the spawn). The settle letter at the waypoint gave +2 families in 2 of 2 clean tries (raid squad); the control is not clean. Command `rebel_raid_rally` added (HarnessActions version 27). See "Raid aimed at the woods" in `implementation-notes/homeless-rebellion.md`.
Part 5 (2026-10-12, live with the user, fresh games): burgage plots and the tent. **Burgage plots can be placed without a mouse**:
set `PawnCPP.placePlotType` 3 and `placeFieldMode` true, write `extractedPlots` (command `plot_field_place`), set `fieldClosed`,
call `addCommitFieldRequest()` (HarnessActions 31). `changePlotOffset(n)` changes the plot count of a field. Construction, move in
and deletes fire no hookable function (poll counts). See `implementation-notes/burgage-placement-events.md`.
The tent is an `SMBuildingMaster` of type 87 that holds the start families (`occupantFamilyIDs`) without slots in its stats row;
a bandit camp is the same model with type 100 and the bandit lord as owner. The plot commit cannot make a tent (it builds a plot).
`demolish(false)` removes the tent; the families stay homeless and wander, and no new tent appears. See `implementation-notes/tent-placement.md`.
Follow-ups (2026-10-13, issue #61): homeless families wait without limit (approval is a one-time step), the settle letter fills every free home slot, `family_add` still crashes (0x3c1), plots on bad ground are accepted. See `implementation-notes/refugee-followups.md`.
Tracking issue: #51 (https://github.com/GarrettGruss/manor-lords-mod/issues/51)

## Goal
Find out how a bandit unit becomes families of the player's village, and make that path testable in the harness.
Players report that when bandits are in their region, they can negotiate with them, and the bandit unit turns into families.
The user confirmed in a local game: negotiation with the bandit faction is offered while bandit units are present.
For the invasion mode this is a second outcome of a raid besides a fight: raiders who join the village as settlers.

## Feature: refugee waves (status: built as mod/RefugeeWaves, scenario refugee-wave passes 3 of 3, 2026-10-13)
A mod event brings a wave of refugee families into the player's region. The refugees stay homeless and lower approval until the
player houses them. If they stay homeless too long, they can turn on the player (the homeless rebellion below).

User design (2026-10-12):
- Refugees must not be housed by the mod. They arrive homeless. The pressure is the approval loss.
- The player resolves the wave by building homes (burgage plots). Families move in by themselves when a plot is finished.
- Every step the mod does must work without the mouse.
- Sources of a wave: a settlement surge (`settleRegion`), bandits who settle after a negotiation (settle letter), and possibly
  families who lose their homes (eject).

### What we know (evidence in `implementation-notes/`)
| Step | Method | Result | Note |
|---|---|---|---|
| Wave source: surge | `PawnCPP:settleRegion` on the player's own, settled region (`settle_region`, camp at `tent_find_spot`) | +5 families and a homeless tent per call; 2 calls: 10 -> 15 -> 20 families; no crash; owner, settled state and houses unchanged | `immigration-surge.md`, `refugee-followups.md`. The 5 families fill free houses first (2 here), the rest (3) go into the tent; a camp in the woods and supply 1 change nothing. |
| Wave source: bandits | Settle letter to raid squads (`bandit_letter raider_suggestSettle+20`, tag `attacking`) | One new family for each FREE HOME SLOT, not per squad: +2 with 2 free slots, +7 and +10 with 7 and 10 (1, 2 or 5 squads) | `refugee-followups.md` (item 4). Needs a raid near the village. The old homeless stay homeless. |
| Wave source: eviction | `Region:SetFamilyHome(id, nil, suppress)` (`family_eject`) | Housed families become homeless at once; the game does not rehouse them by itself in 5 game days (eject late, not in the first game day after a load) | `homeless-refugees.md`, `refugee-followups.md`. `home=tent` moves them into a tent (no capacity limit). The vacant counter is `living - families`, so an eject never changes it. |
| Pressure | Homeless families | A one-time step of about 2 to 3 points per homeless family, reached in about 3 game days (3 homeless: 61, 5: 57, 8: 52 to 54), then flat or slightly up. 20 game days: no starving, no leaving, no rebellion | `refugee-followups.md` (item 1). A food shortage adds its own fall. |
| Natural growth | `Region:GetMonthlyPopGrowthModifiersWithValues` | Base 1, Approval 1 at approval 71; `NoBurgagePlotAvailability` blocks growth | Read by `family_state` (`growth`). |
| Resolution by the player | Build burgage plots | Homeless families move into each plot when it is finished (5 -> 0 homeless in 12 game days); approval 54 -> 66 | `refugee-cycle.md`. |
| Resolution by the mod | `Region:accomodateHomelessFamilies(nil)` (`accommodate_homeless`) | Rehoused 3 ejected families at once when slots existed | For tests or an event end. |
| Bad outcome | Homeless rebellion (`homeless_rebel`, `rebel_raid_rally`) | Families become bandit squads that raid the village | `homeless-rebellion.md`. |
| Test helper | Mouse-free burgage plots (`plot_field_place`, `runlib/plotgeom.py`) | Works. The commit checks nothing: plots in the woods, in the air and on top of houses were all accepted and counted as unbuilt slots | `burgage-placement-events.md`, `refugee-followups.md` (item 7). |
| Not usable | `Region:AddNewFamily` (`family_add`) | New homeless family, then a game crash 1 to 2 game days later (twice: s15-f3 and s61-plots-add with the `adult` option; all members have role 3, Age 1) | `refugee-followups.md` (item 6). Do not use. |
| Not usable | Live `buildingStats` slot writes | Existing buildings ignore them | `tent-slot-limit.md`. |
| Not usable | Placing a tent directly | No mouse-free call; the plot commit builds a burgage plot instead | `tent-placement.md`. `settleRegion` makes tents as a side effect. |
| Detection | Construction, move in, deletes | Fire no hookable function; poll counts (`getBuildingCount`, `getNumHomelessFamilies`) | `burgage-placement-events.md`. |

### Feature plan
1. Event design with the user: trigger (date, approval, random, a letter), wave source and size (number of `settleRegion` calls,
   settled bandits), the camp place (near the village, the woods or the map edge), the rebellion timer, and the message to the player.
2. Mod `RefugeeWave` (own mod and Lua state, `HarnessCommands` registry): start a wave without the mouse, track the wave's families and
   the homeless count each game day, end the wave when they are housed, start the rebellion when the timer runs out. No raw eval.
   Game thread only.
3. Telemetry and metrics: homeless count, approval, wave family ids, wave state.
4. Scenarios: (a) wave, no homes: approval falls, the rebellion starts at the timer; (b) wave, the player builds plots (mouse-free in
   the test): homeless reach 0, the wave ends, approval recovers. Fixtures `base` and `burgage-start`.
5. First close the spike questions that block the design (#61): where the families outside the tent live, why vacant slots do not
   rise after an eject, what happens after day 5.

### Feature open questions
- Trigger, source and size of a wave (user decision).
- Does the feature need `family_eject`, or is `settleRegion` enough (it already makes homeless families)?
- Do surge families count as normal families for food, work and taxes?
- Does a save and load keep the wave state (families, tents)? The mod must not depend on its own memory across loads. (Not testable: save functions are banned.)
- Answered in #61 (see `refugee-followups.md`): homeless families wait without limit, so the rebellion needs the mod's own timer; the settle letter fills all free slots, so cap the free slots before a letter.
- Open: a whole-family `family_add`, a third `settle_region`, water and steep ground for plots, and whether bad plots are ever built.
- Is the rebellion timer better in game days or in approval (for example below 40)?

### Feature acceptance criteria
- [x] The wave design is agreed with the user and written here (accepted 2026-10-12 on #51; built as `mod/RefugeeWaves`, see `implementation-notes/refugee-waves-mod.md`).
- [x] A named command or mod call starts a wave without the mouse; a real run shows +N homeless families (`RefugeeWaves.start_wave`; runs rw1 to rw3: +5 families, +3 homeless).
- [x] A scenario shows approval falling while the wave is homeless, and the wave ending when the player builds homes (`refugee-wave` phase 1, 3 of 3).
- [x] A scenario shows the rebellion starting when the timer ends (`refugee-wave` phase 2, 3 of 3).
- [x] Fake game tests cover the mod (`test_fakegame_refugeewaves.py`). No raw eval. No save function called. No game asset, key or save data in git.

## Reverse direction: homeless families become bandits
Goal: an immigration event brings more people than homes. If the homeless stay unhoused too long, or approval is low, they turn on the player. Find out if the game does it, and make the mod able to show it.
User test idea: remove families, check the family count fell, then spawn a bandit at the homeless tent (or at the house of the removed family).
- Q-R1: Does the base game turn families into bandits or make them leave when approval is low or they are homeless? (answer: no rule found by name; `MLCheatManager:Rebel` exists; base values Approval 71, publicOrder 100)
- Q-R2: What does `sack_people` do to a family: removed from the count, made homeless, or killed? (answer: killed, count falls at once, homeless stays 0, vacant slots rise)
- Q-R3: Can the mod make a bandit unit appear at a chosen point, owned by the bandit faction, and does it act as a raider? Also `turnToBandit`. (answer: yes at a point, idle; `spawnRaiders` with the home as target attacks)
- Q-R4: Conversion ratio, as a proposal: one Brigands squad (18 units) for 2 families.
- Acceptance: removing N families gives bandit units at their homes that attack the village. Met with `homeless_rebel mode=raid` (raiders march in and burn buildings within about 215 game seconds, from the map edge). Met late with `mode=home`: the squads wait about 650 game seconds, then burn. Not met: bandits that attack at once from the home.
- Rally goal (user design): families go into the woods, rally for a while, then attack; the player can negotiate during the rally and turn them back into families. Result of part 3: the rally exists at the AI waypoint (test 2b), the player can end it with the letter (tests 5a to 5c), but the families do not come back for `spawnArmy` rebels, and the rally point cannot be chosen (tests 2 to 4). Fallback: `rebel_rally`, wait, `rebel_fallback_attack` (test 6).
- Named commands: `homeless_rebel`, `bandit_spawn_at`, `bandit_turn` (HarnessActions version 27: plus `bandit_kill_squads`, `forest_spot`, `rebel_raid_rally`). Fake tests: `test_fakegame_harnessrebel.py`. No scenario yet.

## Non-goals
- New UI, new letters or new art.
- Changing raid timing or raid size (spec 10).
- Calling any save function. Changing the user's saves.

## Leads (jmap, 0.8.111)
- `MLCheatManager:SettleRaiders()`: a developer cheat with no parameters. Probably settles the raiders that are present.
- `SMUnit:turnToBandit()`: the opposite direction (a unit becomes a bandit).
- `PawnCPP.isBandit` (the bandit pawn), `RTSMultiEngineCPP:spawnRaiders`, `spawnBanditCamp`, `MLCheatManager:SpawnBanditSquad`.
- `Reward.spawnRaiderForce` (a letter or event reward that spawns raiders).
- Family count: `Region:getTotalNumFamilies()`. Units by side: harness command `units_census`.
- The in-game negotiation is reached from the bandit faction's diplomacy panel (user). Its Blueprint widget and the function it calls are not known.

## Questions
- Q1: What does the in-game negotiation call (widget, function, parameters)? What does it cost (silver, influence, goods)?
- Q2: What happens to the bandit units: are they removed, do they walk to the village, how many families appear (per unit or per squad)?
- Q3: Does `SettleRaiders` do the same thing as the negotiation? With raiders, with a bandit camp squad, with no bandits?
- Q4: Which conditions are needed: bandits inside the player's region, bandits not in combat, a free house, approval, a relation value?
- Q5: Can the mod trigger it with a named command (no raw eval), so a scenario can test "negotiate, then families + N"?

## Plan
1. Load fixture `base` (developed village). Spawn bandits in the player's region (`spawn_units side=bandit`, `spawn_raid` or `spawn_bandit_camp`).
   Read families, homeless, units by side.
2. Find the negotiation path: widget classes and functions about bandits or diplomacy (bridge `list_functions` on the diplomacy widgets,
   hooks on candidate functions while a person uses the UI if needed). Do not click UI by guess.
3. Try `MLCheatManager:SettleRaiders()` with bandits present. Record families, units, silver, influence before and after, and where units go.
4. If a game function works: add a named HarnessActions command (for example `settle_bandits`) and a read command if needed, with fake game tests.
5. Write the findings to `implementation-notes/bandit-settlement.md`.

6. Tent pipeline: place a tent (auto spot, then a click or a game call), check `vacant_slots`, send the settle letter, check that a family lives in the tent.
   Done: `tent_find_spot`, `housing_state`, `building_stat`. Open: a mouse-free placement call, and the pipeline run.
7. Rally in the woods (part 3): `forest_spot`, spawn rebels in the woods, watch the rally, try a move order and a challenge, negotiate during the rally, build the fallback. Done (see the table in `homeless-rebellion.md`). Next: find why raid squads give families and `spawnArmy` squads do not; find a way to choose the rally point (a neighbour lord army as bait is a lead).
8. DONE, result: not possible by a row write (see `implementation-notes/tent-slot-limit.md`). Tent as a home by a live slot limit (part 6, user design 2026-10-12). Idea: make the tent a real home for a short time, let
   immigration fill it, then take the slots away so the families become homeless again (the start of the homeless rebellion).
   - Add a test-only command `building_stat_write` (HarnessHousing): change one number field of one `buildingStats` row in memory,
     for example `occupantTypes.Y` of row 87. Same rules as `datatable_write` (spec 09: an in-memory write that read back, no file).
   - Test on fixture `manor-bailey` (the user's manor fixture). It needs a tent: if it has none, first cause an immigration with no
     free homes so the game puts one up, or use a fresh game (the start tent holds 5 families).
     1. Read `housing_state` (families, homeless, vacant slots, tent families).
     2. Raise row 87 `occupantTypes.Y` (for example 0 -> 5). Read again: do vacant slots rise at once (the game reads the row live),
        only for new tents, or not at all?
     3. Cause an immigration (settle letter or a game event). Check that families move into the tent as housed families.
     4. Lower the limit back to 0. Check what happens to the families in the tent: ejected (homeless again), kept over the limit,
        or something else.
   - Fallback if live writes do nothing: the same change in a pak (`harness-pak-mod`), then compare a game with and without it.
   - Risk: native code treats type 87 specially (spawn on events, delete when homes are free, its families count as homeless).
9. Part 7, homeless refugees (user design 2026-10-12): make homeless families that stay homeless, with `Region:SetFamilyHome(id, nil, suppress)` (eject) and `Region:AddNewFamily` (new families). Status: eject DONE (`family_eject`, runs s15-f1, f2, f4); new families PARTLY (`family_add` crashed the game, run s15-f3); tent as home not tested. See `implementation-notes/homeless-refugees.md`.
10. Part 8, refugee cycle (user design 2026-10-12): eject 5, settle letter, accommodate, 5 burgage plots without the mouse. Status: DONE (runs s15-cyc1, s15-cyc2). The settle letter gave +7 families (not 1 per squad); homeless families moved into each new plot by themselves. See `implementation-notes/refugee-cycle.md`.
11. Part 9, immigration surge (user design 2026-10-12): call `settleRegion` on the player's own settled region, without raid and letter. Status: DONE (run s15-surge1). Each call added 5 families and a new homeless tent (type 87); 2 calls: 10 -> 20 families, 8 homeless, approval 71 -> 54 in 5 days; no crash, no harm seen. See `implementation-notes/immigration-surge.md`.
12. Settler camp through the UI (live with the user, 2026-10-13, run live-camp2): the "Settlement Options" Confirm calls `PawnCPP:settleRegion(region, camp, supply, type, nil)` (Modest = 0, Town = 1). On an empty claimed region one call gave 3 tents, a supply store and 5 families. See `implementation-notes/settler-camp.md`.

## Open questions
- Is the negotiation the same code path for raiders and for bandit camp squads?
- Does the game read `buildingStats` slot counts live, or copy them into each building (part 6)? Answered: not live (tent-slot-limit.md). Open: do new buildings read the changed row when they are placed?
- Can a mod compute burgage plot shapes (corners, house and extension transforms, back facade) for any spot? What does the commit do
  on bad ground (overlap, water, slope, no road)?
- Do settled bandits keep combat equipment or experience?

## Acceptance criteria
- [x] `bandit-settlement.md` answers Q1 to Q5 with evidence (calls, values before and after, screenshots), or "not possible, because" with evidence.
- [ ] If a working call exists: a named command triggers it, a fake game test covers it, and one real run shows families rising and bandit units falling.
  Partly met: commands (`bandit_letter`, `settle_raiders`, `vacant_slots` in `bandit_state`) and fake tests exist. A real run shows bandit units falling and families +1 with vacant slots (s15-c). No scenario yet; a camp unit lured into the region is not tested.
- [x] No game asset, key or save data in git. No save function called.
- [ ] Pipeline "tent -> settle letter -> a family lives in the tent" shown in a real run, with the tent placed by the final mod without the OS mouse. Not met: no tent could be placed (see `tent-placement.md`). Alternative now possible: burgage plots placed without the mouse (part 5).
- [x] Part 6: a live slot limit on the tent row is raised, families move in through immigration, and lowering it changes their state (result recorded either way). Result: NOT POSSIBLE by a live row write. The write works (read back), but vacant slots do not change, no family moves in, and lowering changes nothing. Even a burgage plot row (type 3) is not read live. Runs s15-t1 and s15-t2. See `tent-slot-limit.md`.
- [ ] Rebels rally at a chosen point, can be negotiated with during the rally, then attack. PARTLY met in part 4 (runs s15-p1 to p5): a raid (`rebel_raid_rally`) rallies at the AI waypoint for 50 to 100 game seconds, not at the chosen woods (the target is ignored); the letter during that rally gave +2 families in 2 of 2 clean tries; then it attacks (about 360 to 430 game seconds after the spawn), after it burned 1 to 6 buildings on the way. Open: a rally at a chosen point, and a clean control for squad types. Part 3 result: PARTLY met (run s15-w3, s15-w4): they rally at the AI waypoint (-31000,-22500) inside the player region, not at a chosen point; the letter ends the rally and the attack (units removed, silver taken) but gave no family (3 of 3 tries); the attack starts about 650 game seconds after the spawn. Open: a way to choose the rally point, and the reason why raid squads give families and `spawnArmy` squads do not.
- [ ] Part 7: refugees stay homeless and approval falls, made without the mouse. PARTLY met: `family_eject` (lead 1) works, 3 of 3 runs (s15-f1, f2, f4): 3 families homeless at once, no rehousing in 5 game days, approval 71 to 59. Lead 2 `family_add` made homeless families but the game crashed 2 game days later (s15-f3). Open: tent as new home, a safe family source. See `homeless-refugees.md`.
- [x] Part 8: the refugee cycle runs in one game and every step is recorded (runs s15-cyc1, s15-cyc2): eject 5 (vacant slots stay 2), settle letter +7 families, `accommodate_homeless` no change without free slots, 5 plots placed without the mouse and built in 12 game days, homeless families moved in by themselves (5 to 0). See `refugee-cycle.md`.
- [x] Part 9: `settle_region` on the settled player region adds homeless refugee families (run s15-surge1): +5 families and a new tent per call, 2 calls, approval fell 71 -> 54. `family_state` also reads the monthly growth modifiers (`base`: Base 1, Approval 1). Open: woods or map edge camp, third call, other types. See `immigration-surge.md`.
- [x] A forest point near the village can be read without the mouse (`forest_spot`, run s15-w1). Woods near the village exist (13915 and 14551 units away); the squad does not stay there.
