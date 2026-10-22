# Lead 1.2: stances

Probe: test scenario `probe-lead-stance`. Command `lead_stance` (`SquadComponent:SetBehaviourStance({ Value = id }, stance, false)`).

## Result
- The call works: `call_ok_aggressive` 1 and `call_ok_defensive` 1, with no crash and no error (run 20261021-044002-405f). Stance values: neutral 0, aggressive 1, defensive 2.
- The stance can NOT be read back. `SquadComponent:GetSquad` returns a `Squad` struct by value. Reading it ended the game (run 20261021-041541-74de: crash, exit code 3221226505 = 0xC0000409, at the first `lead_stance` read; same family as `getSquadByID` in the old `baron-model.md`). `HarnessLeads.READ_SQUAD_STRUCT` is now `false` and must stay `false`.
- The effect on the fight is NOT proven. Setup: 1 lord with 3 squads of 32, 2 player squads of 36, challenge. Squad 1 aggressive, squad 2 defensive, squad 3 left alone. After 10 game seconds the alive units were 18, 20 and 32 (the stance squads were already in the fight and the control was not, so the three are not comparable). Both stance squads were gone 10 s later, the control had 31, 25 and 20 at the next reads. One squad (defensive) was listed again at a far position (-38223, -89555) with 18 units at the last read: it may have fled. One run with one squad each is not enough to say that a stance changes the result.
- Screenshots: `evidence/stance-*.jpg` (see `evidence/README.md`). The camera stays at the player village and the fight is out of view, so they prove only that the game ran.

## Bug found in the harness (fixed)
The command parser in `HarnessActions` had no field `stance`, `component`, `mesh` or `restore`. Runs 20261021-042003-6464, 20261021-042156-279e, 20261021-042605-73b3 and 20261021-042758-8c0d never set a stance (the command only read). Only run 20261021-044002-405f called `SetBehaviourStance`. The fields are now in `parseRequest`.

## Risks
- The AI may overwrite the stance. Not measured.
- No read-back: a feature cannot check the stance. It can only call and watch the units.

## Does a mod feature need it?
Possibly a "hold position" order for a baron army (defensive). The effect must first be shown in an A/B test (skill `harness-ab-testing`): same army, stance against no stance, several runs, measure losses and distance moved. Until the owner wants that, the lead stays open.
