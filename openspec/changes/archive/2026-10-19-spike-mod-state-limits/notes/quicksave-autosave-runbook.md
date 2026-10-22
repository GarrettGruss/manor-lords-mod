# Runbook: quick save and autosave keep the pawn Tags (task 1.3)

Change `spike-mod-state-limits`, issue #283. Date: 2026-10-19. Nothing here has run yet. "[agent]" steps are for the agent, "[owner]" steps are for the project owner.
No probe, scenario or script in this runbook calls a save function. The owner saves with the quick save key. The agent never calls `Request Autosave`, `SetAutosavePeriod` or `eval_lua`.

## Facts, with sources

- Start a game that stays open: `uv run python harness\run.py --scenario noop --keep-open --run-id <id>` (`harness/README.md` lines 11, 312; `harness/tools/load_save.py` lines 1-12, 24-30). `noop` is `harness/scenarios/noop.py`.
  - `--new-game` installs no slot. `--fixture base` (or another name in `harness/fixtures/fixtures.json`) installs a copy as `saveGame_<max+1>` in the REAL folder (`harness/README.md` lines 322-328). This runbook uses `--new-game`, so the harness adds no slot.
  - `run.py` deploys the mods first (`harness/runlib/phases.py` line 568), so `InvasionMod` with the feature `mod_state` is installed.
- Files of the run: `runs\<id>\appdata` (private LOCALAPPDATA), `runs\<id>\bridge` (bridge folder, `harness/runlib/runfolder.py` line 75), `runs\<id>\commands` (HarnessActions commands), `runs\<id>\modcmd\InvasionMod` (mod commands, `harness/runlib/commands.py` lines 93-100).
- The game saves and loads only in the REAL folder `%LOCALAPPDATA%\ManorLords\Saved\SaveGames`, also with a private LOCALAPPDATA (`CLAUDE.md` Safety; `harness/README.md` lines 319-320).
- Marker commands, no raw eval: `InvasionMod.mod_state_set` (args `key`, `value` as text, max 60 chars) and `InvasionMod.mod_state_dump` (returns `values`, `tags` = all pawn Tags, `stored_version`). Keys: `selftest_int`, `selftest_flag`, `selftest_text` (`mod/InvasionMod/Scripts/config.lua` lines 7-14; `mod/InvasionMod/Scripts/features/mod_state/init.lua` lines 79-123). The set writes the Tags with `FName` in Lua. The scenario `mod/InvasionMod/scenarios/mod_state/roundtrip.py` does the same.
- After a load, the feature hooks `ReceiveBeginPlay` and reloads the state from the Tags (`init.lua` lines 36-70). The dump after a load shows what came back.
- A menu save and load kept the Tags in an earlier manual check (`openspec/changes/archive/2026-10-15-legacy-24-mod-save-state/implementation-notes/menu-save-check.md`). Quick save and autosave were not tested.

## Autosave: the timer problem

- `HarnessBoot` restarts the pawn autosave timer with a one year period before READY (`mod/shared/HarnessAutosave/HarnessAutosave.lua` lines 6, 84-95). The owner would wait a year.
- The named commands take no period: `disable_autosave` calls `autosave.disable()` with no argument (`mod/HarnessActions/Scripts/main.lua` lines 340-345). No named command sets a short period. Do not change code for this spike.
- Proposed way, not verified in the real game: a structured bridge op (not raw Lua eval) that calls the function HarnessBoot uses, with a short period: `{"op":"call","ref":"first:MLGameInstance","function":"SetAutosavePeriodOnPawn","args":[120]}` (op list: `mcp/ue4ss_bridge/server.py` lines 660-677). `SetAutosavePeriodOnPawn` only restarts the pawn timer. It changes no setting and saves nothing (`openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md`, "What the game has"). Not verified: that the ref `first:MLGameInstance` resolves, and that the float 120 is accepted. If the call fails, stop and ask the owner. Never try the native `SetAutosavePeriod`.
- The timer counts real time, also in a paused game (same note). A new pawn (a load) may reset the timer (same note, "Not done and not verified"). So the agent pushes the timer away again after each load.

## Slots, and what can be overwritten

- Fixed slot names are `autosave` and `menu`. Menu saves are `saveGame_<N>` (`.../legacy-24-mod-save-state/implementation-notes/save-hooks.md` lines 65-74).
- An autosave writes the slot `autosave`, so it overwrites the existing real `autosave.sav`, `autosave_descr.sav` and `autosave_coat_0..5.png` (last seen dated 2026-10-08). The owner loses the old autosave. Only the step 1 backup covers this. Not verified: that an autosave always uses the name `autosave`.
- Quick save slot name: not verified. No note in the repo names it. It may be a fixed name (an earlier quick save is then overwritten) or `saveGame_<N>`. Step 6 finds out by comparing the folder before and after.
- The stale slot `saveGame_48` (task 2.1) is not touched here.
- The load list shows only `autosave` and `saveGame_<N>` (save-hooks.md line 74). Not verified: that a quick save is in the list.

## Guard report of the harness

- With `--keep-open`, `run.py` does not compare the save folder at the end. The run notes say "the user's save files were not compared (--keep-open)" (`harness/runlib/phases.py` lines 528-536). So player saves do not fail this run. Expected: the `noop` run passes. Not verified: the exact summary text.
- `--new-game` installs no slot, so the next run has nothing to remove. The owner saves are in no ledger, so no run deletes them. A later run takes a new snapshot before its own run. Not verified in the real game.

## Steps

1. [agent] Ask the owner to close Manor Lords. Back up the real save folder (never write into the original):
   `Copy-Item -Recurse "$env:LOCALAPPDATA\ManorLords\Saved\SaveGames" "$env:LOCALAPPDATA\ManorLords\Saved\SaveGames-backup-qs-20261019"`
   Keep a list of the folder for steps 6 and 10: `Get-ChildItem "$env:LOCALAPPDATA\ManorLords\Saved\SaveGames" | Select-Object Name,Length,LastWriteTime | Out-File runs\qs-before.txt`
   Check that the backup has the same file count.
2. [agent] Start the game: `uv run python harness\run.py --scenario noop --keep-open --new-game --run-id qs-autosave-1`. Wait until the run ends with the game paused. Read `runs\qs-autosave-1\summary.json` first.
3. [agent] Write the two helper scripts (last section) to files in the scratchpad. Check the timer with HarnessActions: `uv run python harness\tools\s29_command.py qs-autosave-1 "[{\"command\":\"autosave_status\"}]"`. Expect `remaining_s` near 31,535,000.
4. [agent] Write the marker (game stays paused):
   `uv run python <scratchpad>\qs_cmd.py qs-autosave-1 InvasionMod.mod_state_set "{\"key\":\"selftest_text\",\"value\":\"qs_quick_1\"}"`
   `uv run python <scratchpad>\qs_cmd.py qs-autosave-1 InvasionMod.mod_state_set "{\"key\":\"selftest_int\",\"value\":\"4127\"}"`
   `uv run python <scratchpad>\qs_cmd.py qs-autosave-1 InvasionMod.mod_state_dump "{}"`
   Expect the Tags `invasion:selftest_text=qs_quick_1` and `invasion:selftest_int=4127`, one entry per key.
5. [owner] In the game, make a QUICK SAVE with the quick save key (not from the Esc menu). Tell the agent when it is done.
6. [agent] List the save folder again and compare with `runs\qs-before.txt`. Record the new or changed files: this gives the quick save slot name. If an older user file changed (other than a fixed quick save name), stop and tell the owner. The backup restores it.
7. [agent] Change the marker so the autosave test is separate: set `selftest_text` to `qs_auto_1`, dump, check the Tags.
8. [agent] Shorten the timer (not verified): `uv run python <scratchpad>\qs_bridge.py qs-autosave-1 120`. Read the timer with `autosave_status` (step 3 command): expect `remaining_s` about 120 and falling. If the call fails, stop.
9. [owner] Unpause the game and let it run about 3 minutes. Do not save by hand. Tell the agent when the autosave happened.
10. [agent] List the save folder and compare. Expect `autosave.sav` and `autosave_descr.sav` changed. Push the timer away again: `uv run python harness\tools\s29_command.py qs-autosave-1 "[{\"command\":\"disable_autosave\"}]"`.
11. [owner] Load the QUICK SAVE from the game menu (Esc, Load game, or the quick load key). Tell the agent when the game is back in the world.
12. [agent] Dump the Tags (step 4 dump command). Expect `selftest_text=qs_quick_1` and `selftest_int=4127`. Run `disable_autosave` again.
13. [owner] Load the AUTOSAVE from the game menu (Esc, Load game, entry `autosave`). Tell the agent when the game is back in the world.
14. [agent] Dump the Tags again. Expect `selftest_text=qs_auto_1` and `selftest_int=4127`. Run `disable_autosave` again. Check the run logs for errors (path of the mod log copy: not verified).
15. [agent] Write the findings to `openspec/changes/spike-mod-state-limits/notes/quick-autosave-tags.md`: slot names, Tags before and after each load, timer calls, any changed old file. Check task 1.3 off only when both loads gave the right Tags.

## Cleanup

16. [agent] Stop the game: `powershell -File harness\game-close.ps1`. Remove the private appdata: `uv run python harness\tools\fixtures.py remove --appdata runs\qs-autosave-1\appdata`. A `--new-game` run leaves no pak and no installed slot.
17. [owner] Decide about the new save files from steps 5 and 9. Keep them, or let the agent remove ONLY the new slot files that step 6 listed. The old `autosave` can be restored from the backup `SaveGames-backup-qs-20261019`. The agent deletes nothing without a yes. Do not touch `saveGame_48` (task 2.1).
18. [agent] If the owner agrees, remove those files by name, then compare the folder with `runs\qs-before.txt`. Keep the backup until the owner says it can go.

## Helper scripts (write to the scratchpad, run with `uv run python <file>`)

`qs_cmd.py` sends one mod command (`<run id> <Mod.command> <json args>`):

```python
import json, sys
from pathlib import Path
ROOT = Path(r"C:\Users\garre\development\manor-lords-mod")
sys.path.insert(0, str(ROOT / "harness"))
from runlib.commands import ModCommandChannel
run_id, command, args = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
channel = ModCommandChannel(ROOT / "runs" / run_id / "modcmd", timeout_s=30.0)
print(json.dumps(channel.send(command.split(".", 1)[0], command, args)))
```

`qs_bridge.py` calls `SetAutosavePeriodOnPawn` through the bridge op `call` (`<run id> <seconds>`). It reaches the bridge of a `--keep-open` game (`harness/README.md` line 407; env as in `harness/runlib/scenario.py` lines 157-168):

```python
import os, sys
from pathlib import Path
ROOT = Path(r"C:\Users\garre\development\manor-lords-mod")
run_id, seconds = sys.argv[1], float(sys.argv[2])
os.environ["UE4SS_BRIDGE_GAME_DIR"] = r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64"
os.environ["UE4SS_BRIDGE_DATA_DIR"] = str((ROOT / "runs" / run_id / "bridge").resolve())
sys.path.insert(0, str(ROOT / "mcp"))
from ue4ss_bridge import server
print(server.one("call", ref="first:MLGameInstance", function="SetAutosavePeriodOnPawn", args=[seconds]))
```

`qs_cmd.py` serves mod commands only. HarnessActions commands (`autosave_status`, `disable_autosave`) go through `harness\tools\s29_command.py`.

## Risks

- An autosave overwrites the real `autosave` slot. A quick save may overwrite a fixed quick save slot. Only the step 1 backup covers both.
- The short timer is a bridge call never tried in the real game. A wrong call could fail or crash the game (not verified). The agent stops at the first error.
- A load may reset the timer to 600 s. A forgotten `disable_autosave` leads to an unwanted autosave about 10 min later.
- A game crash writes a report into the REAL `Crashes` folder. Run `uv run python harness\tools\collect_crash.py runs\qs-autosave-1` after a crash.
- Never write a Tags array through the bridge `set`. The commands above write with `FName` in Lua.

## Open points (not verified)

- Quick save slot name, and whether it is in the load list.
- `first:MLGameInstance` as a bridge ref, and the float argument of the `call` op.
- Whether quick save and autosave keep the Tags (the question of this task).
- Exact run summary text for `--keep-open`, and the path of the mod log copy.
- Whether the autosave fires while the game is paused (the timer counts in a paused game; the save itself was never observed).
