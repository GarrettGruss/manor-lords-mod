# Bandit settlement: findings (spike, 2026-10-12)

Game 0.8.111. Fixture `base` (day 266, player region Riesenbuckel, 10 families at load).
Runs: `s15-b` (the live session; mod log copied to `runs/s15-tools/mod-final.log`). Screenshots: `runs/s15-tools/a1.png` to `a10.png`, `b1.png`.
All counts below were read with the new commands (`bandit_state`, `bandit_mark`, `bandit_track`) and `units_census`. No save function was called. No crash.

## Short answer
- The negotiation is a **letter**. The player sends the paragraph `raider_suggestSettle+<silver>` to the bandit lord ("Outlaws").
- The units are **not turned into families** in this fixture. The bandit units lose their squad at once and are deleted a few game seconds later.
  Families of the player did not rise in 8 settle events (see Q2). So the claim "bandits become families" is **not confirmed**.
- `MLCheatManager:SettleRaiders` has the same visible effect as an accepted letter, but it is free.

## Q1: What does the negotiation call, and what does it cost?
Path (verified): `Diplomacy` map screen (bottom bar, map button) -> portrait of the bandit lord -> tab `Negotiation` -> drag the paragraph
"Perhaps Silver will convince you to join us" into the letter -> `Send`.
- Widget: `letterCreator_C` (`/Game/UI/Diplomacy/letterCreator`). It calls `AttemptSendConfiguredLetter`, which calls `PawnCPP:sendLetter(recipient, Letter)`.
- A hook on `PawnCPP:sendLetter` showed the call: recipient `PawnCPP_AI_...712` (the bandit lord), `Letter = ["raider_suggestSettle+0"]`.
  An amount is part of the paragraph name: `<paragraph id>+<amount>`. The widget shows an editable amount, default `0s.`.
- The paragraph row is in `DT_Para` (extracted with `pakmod.py`, not committed). Key fields of `raider_suggestSettle`:
  `Category 1` (Negotiation), `descr` "Bribe the raiders into settling, rather than raiding.", `paraPick Amt`, `requiredTags [attacking]`,
  `forbiddenSenderTraits [bandit]`, `forceResponse raider_acceptSettle`, `forceResponse_autoResponse raider_refuseSettle`, `effectAmtParas [settleCost]`.
  `raider_acceptSettle` has `Effects [accept_gift]`. Also there is `raider_greeting` (needs the bandit as sender; not used).
- Cost: the silver of the amount is taken from the player when the letter is processed.
  Silver before -> after: +10: 53 -> 43; +30: 43 -> 13; +40: 313 -> 273. Influence did not change (660).
  The bandit lord's `silver` property rose by a smaller number (5 to 25); it is not a clean copy of the amount.
- The amount is **not checked against a price**. +0 (silver 273 -> 233 in one run, not understood: see open questions), and +9999 with 233 silver (no charge) were also followed by the removal of the raiders.
  The reply letters in the player's inbox always list `raider_acceptSettle` and `raider_refuseSettle`; the order differed (accept first for +0, refuse first for +30, +80, +10) and did not match the result.
- Time: the letter is processed on game time. With the game paused nothing happened (+10, paused: no change until unpause). After unpause the raiders were gone within 4 to 16 s.

## Q2: What happens to the bandit units, and how many families appear?
`bandit_mark` remembered 18 raiders (one `spawn_raiders` squad, role `Soldier`), then `bandit_track` and `units_census` were read every 3 to 5 s.
- t0: 18 units in one squad (side bandit).
- After the letter or the cheat (within about 1 s of game time): 18 units, **no squad** (`squad` 0). `units_census` counts them as side `civil`, role still `Soldier`. Their position does not change.
- 4 to 16 s later: all 18 are `gone` (object invalid). They are not dead (`by_state.dead` does not rise).
- Families of the player (`getTotalNumFamilies` over regions owned by the player), homeless families (`getNumHomelessFamilies`): 12 -> 12, 0 -> 0 in every settle event.
  Husband, Wife and Son counts (all sides): 73, 72, 72 before and after. Region `Nusslohe` snapshot diff: only `isUnderAttack` true -> false and `squadsPresent` lost its 3 squads.
- A first run (spawned Brigands plus the world bandit camp, 54 units, three squads) showed the same: all 54 bandit units were removed, families stayed 10 at that time.
  Families of the player rose 10 -> 11 -> 12 in the following minutes, but the AI villages also rose (Hochweg 16 -> 21), so this is normal growth. It did not follow the events.
- The camp squad of the bandit lord is rebuilt by the game later (two squads of 36 units appeared in Krumme Leite).
- Hooks on `Region:AddNewFamily` and `Region:AddNewFamilyMember` and `SMUnit:turnToBandit` recorded no call (the settle code probably calls them natively, below the hook level).
Verdict: units are deleted. Families gained: 0 in this fixture. Not tested: a village with free houses and a low approval, other fixtures, a real raid that the game spawned itself.

## Q3: Does `SettleRaiders` do the same as the negotiation?
Yes for the units: with raiders (18 and 72 units) and with a camp squad the units lost their squad and were deleted. It needs the game to run; it took effect on the next ticks, not while paused.
It costs nothing and sends no letter. With no bandits present it does nothing (called before any raid in the first run: no change).
It works without the tag `attacking`. Family count: no change, same as the letter.

## Q4: Which conditions are needed?
- Relation tag `attacking` between the player and the bandit lord: needed to see the paragraph. Without it the Negotiation tab is empty (screenshot `a4.png`, also with 54 bandit units in the region);
  with it the paragraph shows (`a8.png`). The tag `at_war` was already set. I added `attacking` with `RTSMultiEngineCPP:addRelationTag(player, banditPawn, "attacking")`.
  Not verified: that the game sets `attacking` itself during a real raid. Spawned raiders (`spawn_raiders`) did not set it.
- The letter works with raiders in or near the player's region. Silver of the amount is needed for the charge; with too little silver nothing is charged but the units were still removed (+80 with 53 silver).
- Not needed (not tested as a limit): free house, approval, influence.

## Q5: Can the mod trigger it with a named command?
Yes. `HarnessActions` version 19:
- `bandit_state`: families, homeless families, bandit units, silver, influence, relation tags (read only).
- `bandit_tag` (`tag`, `remove`): add or remove `attacking`, `acquainted`, `at_war`.
- `bandit_letter` (`paragraphs`): `PawnCPP:sendLetter(banditPawn, ...)` from the player. Only the paragraphs `raider_greeting`, `raider_suggestSettle`, `raider_acceptSettle`, `raider_refuseSettle`, with an optional `+<digits>` amount (at most 6 digits).
- `settle_raiders`: `MLCheatManager:SettleRaiders`.
- `bandit_mark` and `bandit_track`: follow the units.
Python: `actions.bandit_state()`, `bandit_tag()`, `bandit_settle_offer(silver)`, `settle_raiders()`, `bandit_mark()`, `bandit_track()`.
Fake game tests: `harness/tests/test_fakegame_harnessbandits.py` (8 tests). No scenario was written (the feature does not give families, so there is nothing to assert yet).

## Open questions
- Where do families come from in the real game? Try a village with free houses and few families, and a raid that the game spawns by itself (its units may carry a flag that `spawn_raiders` units lack).
- Why did silver fall by 40 for the +0 letter? A late charge of the earlier +40 letter is possible.
- What does `settleCost` equal? The amount was never refused, so no price was found.
- Does the game set `attacking` itself? Watch `bandit_state` during a natural raid.

## Not verified
Reply letters content (only the paragraph ids were read), save and load after a settle, the real mouse path to type an amount (the amount stayed `0s.` in the UI test).

## Vacant slots and settling (2026-10-12, run `s15-c`)
Run `s15-c` (fixture `base`, keep-open, game 0.8.111, speed 3x). Player region "Riesenbuckel" is the object `Nusslohe`. Mod log: `runs/s15-tools/mod-s15c.log`. Helper scripts: `runs/s15-tools/hs.py`, `letter.py`, `go.py`. No crash, no save call.
The user says settling needs free homes. Correction to the first section: the base fixture already had 1 vacant slot (`getAvailableLivingSpace` constructed 1), but 18 bandits gave no family there.

Read calls on the region: `getLivingSpace` and `getAvailableLivingSpace` return `{constructed, unconstructed}`. At start: living 11, available 1, families 10, homeless 0.

### Method that gave vacant slots (method 4: families leave)
`sack_people count=4` (existing command, game calls only): families 10 -> 6, residents 35 -> 23, available constructed 1 -> 5 (living space then 12 because a building finished). No building or tent was added. Not tried: building a burgage plot (needs the OS mouse and goods), homeless tents (type 87 exists in the fixture; no vacant-slot effect checked).
Natural growth control (no bandits, game running 3x): families 7 and residents 26 stayed flat for 4 minutes (readings c1 to c8, d1 to d10).

### Settle tests (game running; read every 10 s)
| Try | Call | Before (families / residents / vacant / silver) | After | Bandit units |
|---|---|---|---|---|
| 1 | fixture camp squad (18) already present, `bandit_tag attacking`, letter `raider_suggestSettle+20` | 6 / 23 / 6 / 83 | 7 / 24 / 5 / 63 after about 50 s; residents 26 after 2 min | 18 -> 0, camp rebuilt 18, then fell to 0 |
| 2 | `spawn_raiders squads=1`, letter `+20` | 7 / 26 / 5 / 63 | 8 / 28 / 4 / 43 within 10 s (residents 29 later) | 18 -> 0 |
| 3 | `spawn_raiders squads=1`, `settle_raiders` (cheat) | 8 / 29 / 4 / 43 | no change, 90 s | 18 -> 0 |
| 4 | `spawn_raiders squads=2`, `settle_raiders` | same | no change | 36 -> 0 |
| 5 | `spawn_bandit_camp` (random place, units not in the player region), letter `+20` | 8 / 29 / 4 / 43 | no change in 2 min; silver 23 (charged) | 18 -> 0 |
Homeless families stayed 0 in all tries. `silver` fell by the amount (20) each time for the letter.

### Result
- The letter with vacant slots gave +1 family (2 to 3 residents) for one squad of 18, in two of two tries with raiders that stood near the player. Each family used one vacant slot.
- The cheat `SettleRaiders` gave 0 families (2 tries). It only deletes the units.
- A camp spawned at a random place gave no family: its units were outside the player region. This matches the players' report (lure the camp unit into the region first). Not tested: a camp raider that really chases a player unit into the region.
- Evidence is small (2 positive tries, the control flat). The first try shows a delay of about 50 s, so wait at least 60 s.
- Not checked: whether 1 family per squad is fixed or depends on vacant slots, approval or the amount; the type of the new family (it may be bandit-themed).
- The comparison of camp unit and `spawn_raiders` unit fields (flag, squad, owner) was not done.

### Code
`bandit_state` regions now have `vacant_slots` and `vacant_slots_unbuilt`. Fake test updated (8 tests pass). No new write command: `sack_people` is the existing way to free slots.
