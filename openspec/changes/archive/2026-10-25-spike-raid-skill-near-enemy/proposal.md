# Proposal: find out if skill 19 makes a player squad raid next to an enemy building

Issue: #495. Follow-up of the archived change `spike-squad-raid-skill` (#492).

## Why

In peacetime with no enemy nearby, `SquadComponent:SetSkillActive(handle, 19, true, false)` set the skill but started no raid (`PawnCPP:isAnySquadRaiding` stayed false). An external native mod turns skill 19 on only after the squad stands within 30 m of an enemy building, in the region of that building. The native raid task picks buildings of the squad's region that belong to an enemy pawn. We do not know if the toggle alone starts a raid in that case.

## Question

When a player squad stands next to a hostile building in a hostile-owned region, does turning on skill 19 (flag false, and separately flag true) make the squad loot or burn? Which Lua call can move a player squad there?

## What Changes

- Look for a reflected move function for player squads and test it.
- Make a hostile building (bandit camp, or a rival region at war) near a player squad, or move the squad to it.
- Turn skill 19 on, observe a few game minutes, turn it off, check the squad stops.
- Findings go in `notes/`. Lasting facts go in the wiki.

## Non-goals

- Control of the raid target from Lua.
- Reading `Squad` structs, `GetSquad`, or any call from the list in DANGEROUS_ACTIONS.md.
- Any save call.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

- Notes in this change folder and wiki facts. No code change.
