# Q1: bodies after the families are removed

Runs `corpses-1`, `corpses-2`, `corpses-5` (fixture `playtest-noai`, game 0.8.111, eval enabled in the game copy of UEBridge `settings.lua`, restored to false).

- `homeless_rebel count=2` in this fixture stops after the removal: "no pawn for side bandit" (no Outlaws pawn until `spawnBanditCamp`). The removal itself works: families 5 -> 3, people 6, `Region.corpses` 6 -> 12.
- The fixture starts with 6 old bodies. They leave the list after about 100 game s and their actors disappear after about 470 game s (run `corpses-2`, t 4768: list 12 -> 6 at 4875, actors 12 -> 6 at 5241).
- New bodies: `VAMP_DefaultUnit_C`, `dead = true`. They lie where the person died, not at the home: 1 500 to 24 000 units from the home.
- Persistence (run `corpses-2`, death at t 4768): in `Region.corpses` until about t 6000 (about 1 230 game s, 30 game days). The actor stays about 370 to 400 game s longer, then it is gone (deadScan 0 at t 6990). No pit is needed. Run `corpses-5` agrees (list empty at t 6095).
- Visible? Not shown. Three crops of the same spot (before death, after `just_die`, after hide) are the same (evidence). The camera at low zoom looks at the horizon, at high zoom a body is a few pixels. Not verified.
- Raw reads: `unit.dead`, `unit.realPos`, `Region.corpses`. The actor location of a body is stale (differs from `realPos`).
- Reading `u.Mesh`, `K2_GetRootComponent` on a body after a long time crashed the game (run `corpses-1`, access violation 0x1e3271628). The cause may be a stale Lua reference: do not keep unit references across game time.
