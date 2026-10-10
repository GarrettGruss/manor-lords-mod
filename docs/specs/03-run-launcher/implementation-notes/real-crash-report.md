# Real crash report (spec 03 and 06 follow-up)

Date: 2026-10-10. Scenario: hidden `selftest-crash` (`harness/scenarios/selftest_crash.py`). It makes the real game crash through the bridge.
It calls no save function. Choose the call with `HARNESS_CRASH_CALL=getItem` (default) or `playEventMessage`.

Runs (in `runs/`, not in git): `crash-getitem` (before the fix), `crash-getitem-keep`, `crash-getitem-2` (after the fix), `crash-playmsg` (after the fix).

## Result

| Check | Result |
|---|---|
| Verdict and exit code | `crash`, exit code 2 (all four runs) |
| Reason | `game process ended during scenario`, `crash.exit_code` 3 |
| `summary.json` written | yes |
| `collect` and `teardown` ran | yes. Phases: scenario `failed` (16 s), collect and teardown `ok`. Total 50 s |
| Game process gone after the run | yes |
| User save folder | 204 files hashed before the first crash and after the last run: identical. The launcher note says "the user's save files did not change" |

## Where the UE crash report lands

**In the user's REAL folder `%LOCALAPPDATA%\ManorLords\Saved\Crashes\UECC-Windows-<id>_0000`, not in the private appdata.**
The crash handler of UE ignores the `LOCALAPPDATA` redirect. The private appdata never had a `Crashes` folder.
Each report folder holds `CrashContext.runtime-xml` (about 49 KB), `CrashReportClient.ini` and `UEMinidump.dmp` (about 0.8 MB).
`CrashContext.runtime-xml` has `<ProcessId>` (the pid of the game) and the call stack.

The old `collect` looked only in the private folder. It copied nothing (`crash/` was empty in `crash-getitem`). This was the bug.

## Bugs found and fixed

1. `collect` did not copy the report. Now `phases.copy_crash_reports` searches the real folder and the private one.
   For safety against reports of another game process (for example a game the user plays), a report is copied only if it is newer than the run start
   and its `<ProcessId>` equals the pid of the game of this run (or the report has no readable id).
   After the fix `crash/UECC-Windows-<id>_0000/` has the 3 files, and `artifacts.crash` and a note ("1 new UE crash report(s) were copied") name it.
2. After a crash UE starts `CrashReportClient.exe`. It stays open and waits for a click. Six of them were left over from earlier probe crashes today.
   `teardown` now stops the `CrashReportClient.exe` processes whose parent pid is the pid of the crashed game
   (note: "1 CrashReportClient process(es) of the crashed game were stopped"). I stopped the old ones by hand.

Unit tests: `test_runlib_phases.py` (`CollectTest`: real folder copy, other pid skipped, private folder still searched, pid read; `TeardownTest`: only the reporter of this game is stopped) and `test_runlib_fixtures.py`.

## UE4SS crash dump (`*.dmp` in `ue4ss\`)

No `*.dmp` appeared in `ue4ss\` in any crash. The UE handler caught the crash first. `copy_new_dumps` copied nothing, which is correct. The code path is only covered by a unit test.

## Root causes (from the call stacks)

Both crashes are access violations inside UE4SS when it converts values for a Lua call, not in the game logic:

- `RTSMultiEngineCPP:getItem(1)`: `push_structproperty` -> `push_softobjectproperty` -> `FSoftObjectPath::operator=`, reading address 0x0.
  The returned `Item` struct has a `droppable` `SoftClassProperty`. UE4SS cannot convert it. Any call that returns a struct with a soft object or soft class field will crash.
- `PawnCPP:playEventMessage("Default", ...)`: `call_ufunction_from_lua` -> `push_nameproperty`, address 0x70. A plain Lua string was given for a `Name` parameter.
  Use `FName("...")` in a Lua mod (as `HarnessActions` does for letters). The bridge cannot pass an `FName`, so this call is not usable through the bridge.
- The earlier catalog said "no crash report". That was only because the collect step looked in the wrong folder.

## Not verified

- A crash during `boot` (before the scenario) was not forced. The same code path copies the report.
- The UE4SS `*.dmp` copy (see above).
- A crash while the user plays another game session at the same time (the pid filter is covered only by a unit test).
