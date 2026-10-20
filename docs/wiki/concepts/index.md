# Pages

* [Engine limits found by spikes](engine-limits.md) - Things the game does not allow from Lua or data, found by spikes and closed as not possible, with the evidence and the reason. Now holds buildings inside the manor bailey.
* [Mod commands and state](mod-commands-and-state.md) - How Python scenarios call into Lua mods through HarnessActions, HarnessCommands and metrics, and how mods keep values in a save with ModState.
* [Run folder and verdicts](run-folder-and-verdicts.md) - What is in runs/<id>/ after a run, the fields of summary.json and config.json, the five verdicts with their exit codes and precedence, and the size limit of the summary.
* [Safety rules](safety-rules.md) - The rules that protect the user's real save folder and the game from harness code, with the guards that enforce them (guarded save_game, autosave push, save hash guard, slot ledger) and the crash-prone calls to avoid.
