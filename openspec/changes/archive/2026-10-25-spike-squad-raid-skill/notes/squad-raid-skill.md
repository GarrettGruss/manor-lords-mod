# Squad raid skill (id 19) from Lua

Run `spike-squad-raid-1` (fixture `base`, kept open, noop scenario, game 0.8.117). The MCP bridge tools pointed to another folder, so calls went through the Python bridge client with `UE4SS_BRIDGE_DATA_DIR=<run>/bridge`. Bridge `call` fields: `ref`, `function`, `args`.

## Verdict
Yes, skill 19 can be read and toggled from Lua with reflected `SquadComponent` functions. No native code is needed. The toggle only sets the skill flag. In peacetime in the own region, it started no visible raid.

## Reflected functions (SquadComponent, `RTSGameManager.SquadComponent`)
| Function | Shape (from calls) |
|---|---|
| `SetSkillActive(handle, skill, enable, flag)` | 4 arguments. Returns true for skill 19 on squad 31. Rally (11) returns false (see wiki). |
| `IsSkillActiveForSquad(handle, skill)` | bool. True after the toggle, false after turning off. |
| `isSkillAvailableForSquad(handle, skill, out)` | 3rd argument is an Out parameter: pass `{}`. Squad 31 (5 men): skill 9 true, 11 false, 19 true. Squad 27 (20 men): 9 false, 11 true, 19 false. |
| `IsSkillVisibleToPlayer(handle, skill)` | Skill 19 is not visible to the player on either squad. Skill 9 is visible for squad 31. |
| `CanRallySquad(handle)`, `IsValidSquad`, `HasActiveUnits`, `GetSquadUnitRole(handle)` | Read only, work. |
`handle` is `{"Value": id}`. Player squad ids: property `PlayerSquadUIOrder` of SquadComponent (array of SquadHandle, was 27 and 31). Related: `PawnCPP:isAnySquadRaiding(out)` (pass `{}`), `PawnCPP:IsSkillActiveForSelectedSquads`, `isSkillAvailableForSelectedSquads`, `getSquadStatus`, `getAllCommandedSquads`. No property holds the skill byte array. `GetSquadUnitCount` returned 0 for a 20-man squad: do not trust it (use `steer_state`).

## What the call did
- Squad 31 (player, 5 units): `SetSkillActive(31, 19, true, false)` returned true, `IsSkillActiveForSquad` true for about 60 s of game time (unpaused). The skill stayed on (not reset by the game).
- The squad walked to a point near the village and stopped (target stayed fixed). It was already walking before the call, so this is not proof of a raid order. Squad 27 (not toggled) also kept moving.
- `PawnCPP:isAnySquadRaiding` stayed false before, during and after. So the flag alone starts no native raid task here.
- Turning it off (`false, false`) returned true, and the skill became inactive. The squad made only a small move.
- Skill 9 and 11 stayed inactive on squad 31.
- No crash, no fire or building change was seen (no building was watched closely).

## Not verified
- A squad in an enemy or bandit region: none was reachable on this fixture.
- Whether the native raid task starts with a real enemy building in range, or needs the flag argument true.
- Whether `SetSkillActive` with flag true differs.
- No unit rally by mouse was done.
- The `rallied` bool and the native byte array were not read.
