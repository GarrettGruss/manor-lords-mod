# Proposal: Spike mod state limits

Issue: #283. Legacy source: `docs/harness/24-mod-save-state/README.md` ("Open questions", "Module design: ModState").

## Why
The mod state lives in `Tags` of the player pawn and the player region. The ModState module is built (`mod/shared/ModState/ModState.lua`). The code rejects an entry longer than the name limit. These checks are still open (spec 24):
- A limit test: many entries, long entries, and the save and load time.
- The Tags of AI lords and buildings (can a feature keep state there?).
- A quick save and an autosave: only a menu save was tested.
- The stale slot `saveGame_48` in the real save folder (8 files, in no ledger, older than this work). The user must say what to do.

## What Changes
- Run a limit test with `save_game` (the only allowed save path) and report the numbers.
- Test the Tags of a lord pawn and of one building type.
- Check what a quick save and an autosave do to the Tags, without calling any save function from a probe.
- Ask the user about `saveGame_48`.

## Non-goals
- A side file (option B). Option C stays unbuilt until the limit test shows Tags are too small.
- New mod features.

## Legacy folders
`docs/harness/24-mod-save-state/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A measured limit adds a requirement to `mod/mod_state` in the implementation pull request.

## Impact
Needs the real game, a fresh backup of the save folder, and the user informed before the first `save_game` call. The autosave check needs the player to save or the game timer; never call `Request Autosave`.
