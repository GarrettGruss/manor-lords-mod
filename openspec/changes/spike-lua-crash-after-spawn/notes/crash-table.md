# Crash table

Source: all `runs/*/crash/UECC-*` folders in the main checkout and in all worktrees under `.claude/worktrees/`, plus the real the real `ManorLords/Saved/Crashes` folder under `%LOCALAPPDATA%` (read only). Parsed by a script (`CrashContext.runtime-xml`): error text, address, call stack, `TimeOfCrash`. Duplicates (same crash GUID, copied into a run folder and still in the real folder) are counted once.

Unique crash reports: **143** (117 with a run folder and mod log, 26 only in the real crash folder). Dates 2026-09-27 to 2026-10-23.

## Signature groups

| Group | Count | Meaning |
|---|---|---|
| A Lua table/heap corruption (garbage Lua pointer in ltable/lapi/lvm) | 53 | Access violation inside the Lua core (`getgeneric`, `mainpositionTV`, `luaH_*`, `lua_getiuservalue`, `rehash`, `callbinTM`) with a garbage pointer (`0xffffffffffffffff`, large odd numbers like `0x25e55dc06e1`). Typical of a corrupted Lua table or heap, not of a bad UObject. |
| B UE4SS UObject wrapper deref (stale or invalid UObject) | 40 | Access violation in the UE4SS UObject wrapper (`push_nameproperty`, `UObjectBase::setup_member_functions`, `AActor` metatable, `UScriptStruct` metamethods, `IsA`, `ProcessEvent`). Typical of a UObject that was freed or never valid (small offsets `0x18`, `0x70`, `0x10`). |
| C game code access violation (UE4SS in stack: no) | 34 | Access violation in game code or in an exception rethrow site (`ManorLords-Win64-Shipping +12787ef`). The top frames carry no symbols. Most have no Lua frame in the stack. |
| C game code access violation (UE4SS in stack: yes) | 4 | Access violation in game code or in an exception rethrow site (`ManorLords-Win64-Shipping +12787ef`). The top frames carry no symbols. Most have no Lua frame in the stack. |
| D other | 1 | Other (empty stack). |
| E engine fatal (LowLevelFatalError) | 8 | Engine `LowLevelFatalError`. All 8 are in the real crash folder, 2026-10-13 to 2026-10-15, no run folder. |
| F abort signal | 3 | Abort signal from `luaD_throw` / `luaG_runerror` (uncaught Lua error in a place that cannot unwind). 3 crashes on 2026-10-17. |

Since 2026-10-22 (the era of the levels, bandit camps and raid work): 19 crashes: A 8, B 5, C 6.

Games running at the same time (estimate from the time ranges of all `mod.log` files, including the crashed game itself): 1 game(s): 56 crashes, 2 game(s): 46 crashes, 3 game(s): 13 crashes, 8 game(s): 1 crashes. The estimate is rough, because a run folder only shows when the log was open. All crash groups appear with 1 game too, so concurrency is not required for a crash.

## Named crashes from the task

| Run | Address | Group | Top frame | Seconds since game start | Last mod log line (not UEBridge) |
|---|---|---|---|---|---|
| 20261024-024700-6523 (banditcamp) | 1ed87797829 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable.c:302] | 487 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=45 game_value=100 (gap 5 s) |
| 20261024-021558-0d65 (banditcamp) | 8 | A | UE4SS!luaH_next() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable.c:353] | 52 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=20 game_value=100 (gap 1 s) |
| levels-first-raid-6 (impl-raid-levels) | 25e55dc06e1 | A | UE4SS!luaH_getshortstr() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable.c:777] | 470 | [InvasionMod.bandits] BANDITS season change 3 to 0 on day 274 (gap 1 s) |
| levels-first-raid-4 (impl-raid-levels) | 18 | B | UE4SS!'RC::LuaMadeSimple::Lua::add_metamethods'::'2'::<lambda_2>::operator()() [D:\a\RE-UE | 487 | [HarnessCommands] InvasionMod request 0016 InvasionMod.invasion_state ok=true (gap 6 s) |
| levels-great-raid-waves-2 (impl-raid-levels) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable.c:302] | 76 | [InvasionMod.invasion] INVASION great wave 1 day=212 squads=15 raiders=448 composition=Brigands-spearMilitia-Brigands-Br (gap 2 s) |

Spike #430 (0x328, 3 bandit camps and a second lord) and the on-screen dialog of 2026-10-23 17:44 are the real-folder crash `REAL:..9B61C12_0000` (address 0x328, group C, no run folder, so no log).

## All crashes (newest first)

Columns: date (local), run (worktree), address, group, first non-system frame, seconds since game start, gap in seconds from the last non-bridge mod log line to the crash, games at once, last non-bridge mod log line.

| Date | Run (worktree) | Address | Grp | First frame | Up s | Gap s | Games | Last mod log line |
|---|---|---|---|---|---|---|---|---|
| 10-23 22:14 | REAL:A0A88A6_0000 (localappdata) | 10 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 116 |  | 0 | (no run folder) |
| 10-23 22:01 | 20261024-025737-e905 (armsbutton) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff7c6ed0000 + 11d623a  | 197 | 1 | 2 | [HarnessCommands] InvasionMod request 0127 InvasionMod.liege_state ok=true |
| 10-23 21:55 | 20261024-024700-6523 (banditcamp) | 1ed87797829 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 487 | 5 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=45 game_value=100 |
| 10-23 21:55 | 20261024-025200-6707 (armsbutton) | 18d903438a9 | C | ManorLords-Win64-Shipping 0x00007ff7ed530000 + 12787ef  | 184 | 2 | 3 | [HarnessCommands] InvasionMod request 0168 InvasionMod.liege_menu_state ok=true |
| 10-23 21:17 | 20261024-021558-0d65 (banditcamp) | 8 | A | UE4SS!luaH_next() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable | 52 | 1 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=20 game_value=100 |
| 10-23 19:16 | 20261024-001433-dca8 (impl-start-kit) | 9 | B | UE4SS!RC::Unreal::FField::GetClass() [D:\a\RE-UE4SS\RE-UE4SS\deps\firs | 80 | 1 | 2 | [HarnessCommands] InvasionMod request 0051 InvasionMod.liege_menu_state ok=true |
| 10-23 19:11 | 20261024-001022-bc20 (impl-start-kit) | 1e31605a8 | B | UE4SS!RC::Unreal::UObject::ProcessEvent() [D:\a\RE-UE4SS\RE-UE4SS\deps | 78 | 2 | 2 | [HarnessCommands] InvasionMod request 0003 InvasionMod.liege_menu_state ok=true |
| 10-23 19:08 | 20261024-000543-7e50 (impl-start-kit) | 1e31605a8 | C | ManorLords-Win64-Shipping 0x00007ff6f6100000 + 12787ef  | 134 | 1 | 2 | [HarnessCommands] InvasionMod request 0086 InvasionMod.liege_menu_state ok=true |
| 10-23 18:52 | 20261023-235123-7915 (impl-bandit-order) | 646166a5 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 17 | 5 | 1 | [HarnessLogTest] heartbeat 3 v1 |
| 10-23 18:36 | levels-first-raid-6 (impl-raid-levels) | 25e55dc06e1 | A | UE4SS!luaH_getshortstr() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src | 470 | 1 | 3 | [InvasionMod.bandits] BANDITS season change 3 to 0 on day 274 |
| 10-23 18:23 | q3-first-raid-base-182209 (impl-noai) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 35 | 24 | 3 | [HarnessLogTest] heartbeat 6 v1 |
| 10-23 18:01 | levels-first-raid-4 (impl-raid-levels) | 18 | B | UE4SS!'RC::LuaMadeSimple::Lua::add_metamethods'::'2'::<lambda_2>::oper | 487 | 6 | 3 | [HarnessCommands] InvasionMod request 0016 InvasionMod.invasion_state ok=true |
| 10-23 17:53 | 20261023-225157-5996 (impl-menu-pause) | 156 | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 37 | 3 | 2 | [InvasionMod.scenario_settings] disable_autosave sent |
| 10-23 17:44 | REAL:9B61C12_0000 (localappdata) | 328 | C | ManorLords_Win64_Shipping | 384 |  | 2 | (no run folder) |
| 10-23 17:44 | levels-great-raid-waves-2 (impl-raid-levels) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 76 | 2 | 3 | [InvasionMod.invasion] INVASION great wave 1 day=212 squads=15 raiders=448 composition=Bri |
| 10-22 21:14 | 20261023-021314-dec3 (feat-add-vassal-sack-w) | 281d1c362f1 | A | UE4SS!luaH_getshortstr() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src | 98 | 0 | 1 | [InvasionMod.vassals] VASSALS lost slot=1 region=Goldhof families=16 reason=wiped |
| 10-22 21:12 | 20261023-021121-70f6 (feat-add-vassal-sack-w) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff643a90000 + 12787ef  | 81 | 6 | 1 | [HarnessActions] command 0001 regions_state ok=true |
| 10-22 20:11 | 20261023-010958-4796 (feat-add-vassal-sack-w) | 4455 | A | UE4SS!luaV_execute() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lvm | 64 | 0 | 1 | [InvasionMod.vassals] VASSALS wiped region=Goldhof ruins needed=28 of 34 buildings, villag |
| 10-22 19:54 | 20261023-005320-e91a (feat-add-vassal-sack-w) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff643a90000 + 12787ef  | 51 | 2 | 1 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=42 game_value=100 |
| 10-21 23:27 | 20261022-042514-3045 (feat-add-vassal-sack-w) | 2c | C | ManorLords-Win64-Shipping 0x00007ff76cbf0000 + 12787ef  | 120 | 1 | 1 | [InvasionMod.vassals] VASSALS lost slot=1 region=Eichenhau families=5 reason=wiped |
| 10-21 22:39 | 20261022-033548-7c30 (night-update-raid-cloc) | 70 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 199 | 12 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=71 game_value=100 |
| 10-21 22:39 | ptt-soak-2 (night-spike-playtest-t) | 14e | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 120 | 14 | 3 | [InvasionMod.invasion] INVASION difficulty prompt day=212 current=1 shown=true |
| 10-21 22:31 | 20261022-033050-8596 (agent-a5f108a4e3c11e8d) | 70 | B | UE4SS!'RC::LuaType::XMulticastDelegateProperty::setup_member_functions | 57 | 1 | 2 | [InvasionMod.menu] bottom bar button clicked: raid |
| 10-21 20:46 | 20261022-014538-68e7 (impl-373) | 85 | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 12 | 1 | 2 | [HarnessLogTest] heartbeat 3 v1 |
| 10-21 13:50 | REAL:25682B9_0000 (localappdata) | 18 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 1784 |  | 0 | (no run folder) |
| 10-21 00:14 | 20261021-051155-a6a4 (feat-add-vassal-sack-w) | ffffffffffffffff | B | UE4SS!RC::Unreal::UObjectBase::IsA() [D:\a\RE-UE4SS\RE-UE4SS\deps\firs | 127 | 1 | 1 | [InvasionMod.vassals.probe] PROBE kill start Eichenhau count=1000 |
| 10-21 00:11 | 20261021-050845-d295 (feat-add-vassal-sack-w) | 1e3000050 | C | ManorLords-Win64-Shipping 0x00007ff785ff0000 + 12787ef  | 131 | 6 | 2 | [HarnessCommands] InvasionMod request 0014 InvasionMod.probe_region ok=true |
| 10-21 00:09 | s343-d2 (feat-spike-bandit-mess) | 60 | C | ManorLords-Win64-Shipping 0x00007ff616f50000 + 12787ef  | 90 | 12 | 2 | [HarnessActions] command 0008 bandit_letter ok=true |
| 10-20 22:15 | 20261021-031455-c1ae (agent-ae64f2e6f64074a4) | 2231f0d6c59 | C | ManorLords-Win64-Shipping 0x00007ff6e2c30000 + 12787ef  | 11 | 6 | 1 | [HarnessLogTest] heartbeat 2 v1 |
| 10-20 02:34 | s286-soak-1 (agent-a171b41fd870c087) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 1376 | 1 | 1 | [InvasionMod.sack_and_terms] SACK step people |
| 10-19 22:23 | 20261020-032210-98e1 (agent-adddd1a00c25e6da) | 198a6828f21 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 88 | 2 | 1 | [HarnessCommands] InvasionMod request 0088 InvasionMod.tech_tree_widget_state ok=true |
| 10-18 12:35 | 20261018-173210-49ed (fix-widget-click) | 2ed0241da81 | A | UE4SS!luaH_getshortstr() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src | 215 | 1 | 1 | [HarnessCommands] InvasionMod request 0290 InvasionMod.tech_tree_widget_state ok=true |
| 10-18 12:31 | 20261018-172912-2d86 (fix-widget-click) | 26e7c01cf11 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 138 | 1 | 1 | [HarnessCommands] InvasionMod request 0164 InvasionMod.tech_tree_widget_state ok=true |
| 10-18 12:25 | 20261018-172159-771e (fix-widget-click) | 10a | A | UE4SS!lua_setiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 230 | 1 | 2 | [HarnessCommands] InvasionMod request 0256 InvasionMod.tech_tree_widget_state ok=true |
| 10-18 11:46 | 20261018-164600-7b02 (fix-widget-click) | 2c4 | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 36 | 1 | 1 | [HarnessCommands] InvasionMod request 0001 InvasionMod.tech_tree_widget_close ok=true |
| 10-18 10:41 | 20261018-154053-d9be (M12-tech-menu-f9-hang) | 2160edc9b31 | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 36 | 1 | 1 | [HarnessCommands] InvasionMod request 0001 InvasionMod.tech_tree_widget_state ok=true |
| 10-18 09:12 | 20261018-141126-1361 (M13-manor_stronghold-0) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff6f2220000 + 11d621f  | 53 | 17 | 2 | [HarnessBoot] state -> READY |
| 10-18 06:18 | 20261018-110435-6c0f-013-combat-le (29-custom-units-spike) | 21030 | A | UE4SS!lua_getiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 10 | 3 | 1 | [HarnessLogTest] heartbeat 2 v1 |
| 10-18 05:20 | 20261018-101743-0194 (M02-invasion-07) | Unhandled Except | B | UE4SS!RC::LuaMadeSimple::Lua::get_string() [D:\a\RE-UE4SS\RE-UE4SS\dep | 136 | 1 | 1 | [InvasionMod.sack_and_terms] SACK step people |
| 10-18 05:11 | 20261018-101043-467e (M10-finite_resources-0) | 103 | C | ManorLords-Win64-Shipping 0x00007ff648700000 + 12787ef  | 12 | 3 | 1 | [HarnessLogTest] heartbeat 3 v1 |
| 10-18 04:37 | 20261018-093533-4f17 (M07-vassals-04) | ffffffffffffffff | A | UE4SS!callbinTM() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltm.c: | 117 | 1 | 3 | [HarnessCommands] InvasionMod request 0029 InvasionMod.vassals_lose ok=true |
| 10-18 04:33 | 20261018-093104-446f (M07-vassals-04) | d18 | C | ManorLords_Win64_Shipping | 104 | 3 | 1 | [HarnessActions] command 0005 close_popups ok=true |
| 10-18 04:17 | 20261018-091643-abc3 (M07-vassals-03) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff7cc220000 + 12787ef  | 46 | 1 | 1 | [HarnessCommands] InvasionMod request 0011 InvasionMod.vassals_state ok=true |
| 10-18 03:54 | 20261018-085046-c0e4 (M06-sack_and_terms-03) | 50 | C | ManorLords_Win64_Shipping | 229 | 1 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=40 game_value=90 |
| 10-18 03:50 | 20261018-084900-afca (M06-sack_and_terms-03) | 50 | C | ManorLords_Win64_Shipping | 79 | 4 | 2 | [HarnessCommands] InvasionMod request 0014 InvasionMod.fallback_move ok=false |
| 10-18 03:46 | 20261018-084541-2b07 (M06-sack_and_terms-03) | 50 | C | ManorLords_Win64_Shipping | 65 | 3 | 2 | [HarnessCommands] InvasionMod request 0013 InvasionMod.fallback_move ok=false |
| 10-18 03:19 | 20261018-081831-22dd (M09-refugees-02) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 51 | 1 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=50 game_value=71 |
| 10-18 03:17 | 20261018-081339-1665 (M09-refugees-02) | 6574617494 | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 248 | 1 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=61 game_value=100 |
| 10-18 02:57 | 20261018-075649-b14b (M12-tech_tree-02) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff614ed0000 + 12787ef  | 40 | 1 | 2 | [HarnessCommands] InvasionMod request 0002 InvasionMod.tech_tree_widget_open ok=true |
| 10-18 00:59 | 20261018-055825-d24f (M02-invasion-06) | 67 | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 24 | 5 | 2 | [HarnessLogTest] heartbeat 5 v1 |
| 10-18 00:03 | 20261018-050233-020f (M06-sack_and_terms-01) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 42 | 1 | 2 | [InvasionMod.sack_and_terms] SACK step goods |
| 10-18 00:02 | 20261018-050025-734b (M06-sack_and_terms-01) | ffffffffffffffff | C | ManorLords-Win64-Shipping 0x00007ff7bcd00000 + 12787ef  | 91 | 2 | 2 | [HarnessActions] command 0001 sack_census ok=true |
| 10-17 23:12 | 20261018-041200-e3d8 (M03-raid_behavior-02) | 70 | B | UE4SS!'RC::LuaType::ObjectBase<RC::Unreal::UObject,RC::LuaMadeSimple:: | 26 | 17 | 1 | [HarnessLogTest] heartbeat 6 v1 |
| 10-17 19:37 | 20261018-003552-dbb6 (M05-unit_balance-02) | 70 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 92 | 1 | 2 | [HarnessActions] command 0012 close_popups ok=true |
| 10-17 19:34 | 20261018-003210-bf14 (M05-unit_balance-02) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 139 | 2 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=71 game_value=100 |
| 10-17 19:31 | 20261018-003005-9fe5 (M05-unit_balance-02) | 80 | A | UE4SS!lua_rawgeti() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lapi | 103 | 3 | 2 | [InvasionMod.raid_behavior] RAID_BEHAVIOR loot returned amount=1 good=216 store=2147464203 |
| 10-17 19:29 | 20261018-002714-5f17 (M05-unit_balance-02) | 90 | A | UE4SS!lua_rawgeti() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lapi | 144 | 2 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=62 game_value=100 |
| 10-17 19:23 | 20261018-002116-ba79 (M05-unit_balance-02) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 138 | 1 | 2 | [HarnessCommands] InvasionMod request 0016 InvasionMod.raid_behavior_state ok=true |
| 10-17 19:20 | 20261018-001924-a645 (M05-unit_balance-02) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 39 | 2 | 2 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=205 id=1 state=active living=32 loot=0 loote |
| 10-17 19:10 | 20261018-000904-8756 (M05-unit_balance-02) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 65 | 2 | 2 | [HarnessActions] command 0004 close_popups ok=true |
| 10-17 19:08 | 20261018-000207-d979 (M05-unit_balance-02) | 18 | B | UE4SS!'RC::LuaMadeSimple::Lua::add_metamethods'::'2'::<lambda_2>::oper | 392 | 2 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=16 game_value=100 |
| 10-17 18:55 | 20261017-235321-d86c (M05-unit_balance-02) | 18 | A | UE4SS!lua_rawgeti() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lapi | 120 | 1 | 2 | [HarnessActions] command 0026 close_popups ok=true |
| 10-17 18:53 | 20261017-235133-4f64 (M05-unit_balance-02) | Abort signal rec | F | UE4SS!luaD_throw() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ldo.c | 85 | 1 | 2 | [HarnessActions] command 0015 close_popups ok=true |
| 10-17 18:51 | 20261017-234946-d78a (M05-unit_balance-02) | Abort signal rec | F | UE4SS!luaD_throw() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ldo.c | 85 | 0 | 2 | [HarnessActions] command 0015 close_popups ok=true |
| 10-17 18:36 | fix-b4 (fix-long-run-crash) | ea | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 369 | 2 | 3 | [HarnessActions] command 0117 close_popups ok=true |
| 10-17 18:34 | 20261017-233220-7b9e (M05-unit_balance-02) | ffffffffffffffff | A | UE4SS!luaH_set() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable. | 103 | 0 | 2 | [HarnessActions] command 0019 close_popups ok=true |
| 10-17 18:28 | 20261017-232515-dd45 (M05-unit_balance-02) | a | A | UE4SS!lua_getiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 174 | 2 | 2 | [HarnessActions] command 0039 close_popups ok=true |
| 10-17 18:17 | fix-b2 (fix-long-run-crash) | a | A | UE4SS!lua_getiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 443 | 6 | 2 | [HarnessActions] command 0146 close_popups ok=true |
| 10-17 18:09 | fix-b1 (fix-long-run-crash) | 9 | C | ManorLords-Win64-Shipping 0x00007ff71c240000 + 12787ef  | 535 | 2 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=56 game_value=100 |
| 10-17 18:05 | 20261017-230407-2b72 (M05-unit_balance-02) | 18 | A | UE4SS!rehash() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable.c: | 75 | 2 | 3 | [HarnessActions] command 0010 close_popups ok=true |
| 10-17 18:04 | 20261017-230248-2b3a (M05-unit_balance-02) | 9c | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 44 | 0 | 3 | [HarnessBoot] state -> PAUSING |
| 10-17 17:54 | fix-a2 (fix-long-run-crash) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 323 | 0 | 2 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=254 id=1 state=active living=18 loot=0 loote |
| 10-17 17:53 | 20261017-225038-725a (M05-unit_balance-02) | dc | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 159 | 1 | 2 | [HarnessActions] command 0025 close_popups ok=true |
| 10-17 17:50 | 20261017-224829-53cb (M05-unit_balance-02) | ffffffffffffffff | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 99 | 3 | 2 | [HarnessCommands] InvasionMod request 0005 InvasionMod.invasion_state ok=true |
| 10-17 17:44 | 20261017-224337-9922 (M05-unit_balance-02) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 64 | 3 | 3 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=205 id=1 state=active living=294 loot=0 loot |
| 10-17 17:41 | 20261017-224035-7783 (M05-unit_balance-02) | 11c | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 34 | 2 | 3 | [HarnessBoot] intro cinematic is playing; waiting for it to end before pauseGame |
| 10-17 17:40 | 20261017-223918-7646 (M05-unit_balance-02) | Unhandled Except | C | ManorLords-Win64-Shipping 0x00007ff6e3340000 + 11d621f  | 63 | 2 | 3 | [HarnessCommands] InvasionMod request 0006 InvasionMod.invasion_state ok=true |
| 10-17 17:33 | 20261017-223238-9640 (M04-bandits-02) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 43 | 4 | 1 | [HarnessCommands] InvasionMod request 0002 InvasionMod.bandits_state ok=true |
| 10-17 17:32 | 20261017-223036-5d4e (M04-bandits-02) | 10e | C | ManorLords-Win64-Shipping 0x00007ff78d7e0000 + 12787ef  | 112 | 3 | 2 | [HarnessActions] command 0018 close_popups ok=true |
| 10-17 17:29 | 20261017-222814-b61c (M04-bandits-02) | 1e10f8d8a61 | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 92 | 5 | 2 | [InvasionMod.bandits] BANDITS game rewrote order mod_value=71 game_value=100 |
| 10-17 17:24 | 20261017-222043-cfeb (M04-bandits-02) | 70 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 181 | 3 | 2 | [HarnessActions] command 0023 close_popups ok=true |
| 10-17 17:19 | lead-third-4 (main) | ffffffffffffffff | A | UE4SS!luaH_set() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltable. | 112 | 2 | 2 | [HarnessActions] command 0027 close_popups ok=true |
| 10-17 16:51 | lead-third-1 (main) | Unhandled Except | B | UE4SS!RC::LuaMadeSimple::Lua::get_string() [D:\a\RE-UE4SS\RE-UE4SS\dep | 345 | 1 | 2 | [HarnessActions] command 0115 close_popups ok=true |
| 10-17 16:38 | 20261017-213728-57b9 (M04-bandits-01) | Abort signal rec | F | UE4SS!luaD_throw() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ldo.c | 54 | 17 | 1 | [HarnessLogTest] heartbeat 6 v1 |
| 10-17 01:32 | 20261017-060551-d673-008-raid-beha (M03-raid_behavior-01) | Unhandled Except | B | UE4SS!''RC::LuaMadeSimple::Lua::new_metatable<RC::LuaType::AActor>'::' | 103 | 4 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=211 id=1 state=active living=36 loot=18 loot |
| 10-17 00:17 | m03-bisect2-units-1 (M03-raid_behavior-01) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 233 | 3 | 1 | [HarnessActions] command 0036 close_popups ok=true |
| 10-16 23:47 | 20261017-042002-f474-009-raid-beha (M03-raid_behavior-01) | ffffffffffffffff | A | UE4SS!lua_getiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 191 | 1 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=220 id=1 state=active living=34 loot=32 loot |
| 10-16 23:33 | 20261017-042002-f474-005-raid-beha (M03-raid_behavior-01) | 9 | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 38 | 1 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=205 id=1 state=active living=36 loot=0 loote |
| 10-16 23:29 | 20261017-042002-f474-003-raid-beha (M03-raid_behavior-01) | 43 | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 120 | 2 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=213 id=1 state=active living=35 loot=0 loote |
| 10-16 23:27 | 20261017-042002-f474-002-raid-beha (M03-raid_behavior-01) | 2 | A | UE4SS!luaV_execute() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lvm | 203 | 4 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=221 id=1 state=active living=35 loot=0 loote |
| 10-16 22:04 | 20261017-023205-8036-007-raid-beha (M03-raid_behavior-01) | cb | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 187 | 3 | 1 | [HarnessActions] command 0027 close_popups ok=true |
| 10-16 21:33 | 20261017-023205-8036-001-raid-beha (M03-raid_behavior-01) | ffffffffffffffff | A | UE4SS!getgeneric() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltabl | 77 | 2 | 1 | [InvasionMod.raid_behavior] RAID_BEHAVIOR day=209 id=1 state=active living=18 loot=18 loot |
| 10-16 21:23 | 20261017-014336-0886-012-raid-beha (M03-raid_behavior-01) | 3c8 | A | UE4SS!lua_rawget() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lapi. | 222 | 5 | 1 | [HarnessActions] command 0036 close_popups ok=true |
| 10-16 21:19 | 20261017-014336-0886-011-raid-beha (M03-raid_behavior-01) | Unhandled Except | B | UE4SS!RC::LuaMadeSimple::Lua::get_string() [D:\a\RE-UE4SS\RE-UE4SS\dep | 171 | 3 | 1 | [HarnessActions] command 0025 close_popups ok=true |
| 10-16 21:09 | 20261017-014336-0886-008-raid-beha (M03-raid_behavior-01) | 44 | A | UE4SS!lua_getiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 136 | 4 | 1 | [HarnessActions] command 0020 close_popups ok=true |
| 10-16 21:06 | 20261017-014336-0886-007-raid-beha (M03-raid_behavior-01) | ffffffffffffffff | A | UE4SS!lua_rawgeti() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\lapi | 138 | 6 | 1 | [HarnessActions] command 0020 close_popups ok=true |
| 10-16 20:56 | 20261017-014336-0886-004-raid-beha (M03-raid_behavior-01) | Unhandled Except | B | UE4SS!RC::LuaMadeSimple::Lua::get_string() [D:\a\RE-UE4SS\RE-UE4SS\dep | 193 | 3 | 1 | [HarnessActions] command 0028 close_popups ok=true |
| 10-16 20:48 | 20261017-014336-0886-002-raid-beha (M03-raid_behavior-01) | ffffffffffffffff | A | UE4SS!mainpositionTV() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\l | 81 | 2 | 1 | [HarnessActions] command 0004 close_popups ok=true |
| 10-16 18:08 | 20261016-230828-f23b (M01-mod_state-01) | c | A | UE4SS!luaH_getint() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\src\ltab | 0 | 1 | 1 | [SaveProbe] hooked /Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:LoadGame |
| 10-15 22:56 | 20261016-035535-ce40 (24-mod-save-state) | 530 | C | ManorLords_Win64_Shipping | 25 | 4 | 1 | [HarnessBoot] intro cinematic is playing; waiting for it to end before pauseGame |
| 10-15 22:52 | 20261016-035156-5423 (24-mod-save-state) | 530 | C | ManorLords_Win64_Shipping | 24 | 0 | 1 | [HarnessLogTest] heartbeat 4 v1 |
| 10-15 22:48 | 20261016-034750-d8b4 (24-mod-save-state) | 530 | C | ManorLords-Win64-Shipping 0x00007ff78a010000 + 12787ef  | 24 | 4 | 1 | [HarnessBoot] intro cinematic is playing; waiting for it to end before pauseGame |
| 10-15 22:47 | 20261016-034717-fc52 (24-mod-save-state) | 530 | C | ManorLords-Win64-Shipping 0x00007ff78a010000 + 12787ef  | 26 | 1 | 1 | [HarnessLogTest] heartbeat 4 v1 |
| 10-15 22:43 | 20261016-034223-9e92 (24-mod-save-state) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 37 | 2 | 1 | [HarnessLogTest] heartbeat 6 v1 |
| 10-15 17:37 | s116-hs2 (main) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 787 | 465 | 1 | [RefugeeWaves] wave ended: rebelled |
| 10-15 17:21 | s116-hs (main) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 231 | 196 | 1 | [HarnessLogTest] heartbeat 6 v1 |
| 10-15 14:25 | REAL:C202FEE_0000 (localappdata) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 270 |  | 0 | (no run folder) |
| 10-14 19:10 | s90c-4 (agent-a3d15a7c04573ce6) | 10 | C | ManorLords-Win64-Shipping 0x00007ff634400000 + 12787ef  | 61 | 1 | 1 | [HarnessActions] command 0014 family_add ok=false |
| 10-14 19:08 | s90c-3 (agent-a3d15a7c04573ce6) | 10 | C | ManorLords-Win64-Shipping 0x00007ff634400000 + 12787ef  | 56 | 1 | 1 | [HarnessActions] command 0015 family_add ok=false |
| 10-13 23:07 | s90-6 (agent-afbc0b23214f7573) | 10 | C | ManorLords-Win64-Shipping 0x00007ff7b1660000 + 12787ef  | 62 | 1 | 1 | [HarnessActions] command 0015 family_add ok=false |
| 10-12 23:06 | s61-plots-add (main) | 3c1 | C | ManorLords_Win64_Shipping | 118 | 7 | 8 | [HarnessActions] command 0034 sack_census ok=true |
| 10-12 19:09 | REAL:EF8135B_0000 (localappdata) | 3c1 | C | ManorLords_Win64_Shipping | 78 |  | 0 | (no run folder) |
| 10-12 11:38 | REAL:49CBBBD_0000 (localappdata) | 1f0 | C | ManorLords_Win64_Shipping | 428 |  | 0 | (no run folder) |
| 10-11 22:36 | s14-piece-1 (main) | 10 | B | UE4SS!'RC::LuaType::UObjectBase<RC::Unreal::UObject,RC::LuaType::UObje | 739 | 1 | 1 | [HarnessActions] command 0053 path_state ok=true |
| 10-11 22:22 | s14-wall-u-load-1 (main) | Unhandled Except | C | ManorLords_Win64_Shipping | 691 | 1 | 1 | [HarnessActions] command 0017 kill_units ok=true |
| 10-11 21:54 | s14-path-new-3 (main) | Unhandled Except | C | ManorLords_Win64_Shipping | 978 | 3 | 1 | [HarnessActions] command 0846 wall_state ok=true |
| 10-11 17:55 | REAL:73349C5_0000 (localappdata) | 50 | B | ManorLords_Win64_Shipping | 186 |  | 0 | (no run folder) |
| 10-11 17:47 | REAL:C0822EB_0000 (localappdata) | 50 | B | ManorLords_Win64_Shipping | 95 |  | 1 | (no run folder) |
| 10-11 17:37 | s13-lords-3 (main) | 34c | C | ManorLords_Win64_Shipping | 47 | 1 | 1 | [HarnessActions] command 0005 lord_start_ai ok=true |
| 10-11 17:35 | s13-lords-2 (main) | 34c | C | ManorLords_Win64_Shipping | 177 | 0 | 1 | [HarnessActions] loaded version 15, waiting for C:\Users\garre\development\manor-lords-mod |
| 10-11 17:31 | s13-lords-1 (main) | 34c | C | ManorLords_Win64_Shipping | 248 | 1 | 1 | [HarnessActions] command 0005 lord_relations ok=true |
| 10-10 23:27 | REAL:1077D6E_0000 (localappdata) | 40 | B | UE4SS!'RC::LuaType::UStruct::setup_member_functions<0>'::'2'::<lambda_ | 1040 |  | 0 | (no run folder) |
| 10-10 04:37 | probe-clock-7 (main) | d9 | A | UE4SS!lua_setiuservalue() [D:\a\RE-UE4SS\RE-UE4SS\deps\first\LuaRaw\sr | 31 | 1 | 1 | [HarnessLogTest] heartbeat 5 v1 |
| 10-10 04:04 | REAL:EA1B220_0000 (localappdata) | 10 | B | UE4SS!RC::LuaType::TLuaStringBase<RC::Unreal::FString,RC::LuaType::FSt | 51 |  | 0 | (no run folder) |
| 10-10 03:52 | crash-playmsg (main) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 29 | 0 | 1 | [HarnessLogTest] heartbeat 5 v1 |
| 10-10 03:51 | crash-getitem-2 (main) | Unhandled Except | B | UE4SS!RC::Unreal::FString::operator=() [D:\a\RE-UE4SS\RE-UE4SS\deps\fi | 31 | 1 | 1 | [HarnessLogTest] heartbeat 5 v1 |
| 10-10 03:49 | REAL:E46C106_0000 (localappdata) | Unhandled Except | B | UE4SS!RC::Unreal::FString::operator=() [D:\a\RE-UE4SS\RE-UE4SS\deps\fi | 29 |  | 1 | (no run folder) |
| 10-10 03:48 | REAL:A64BE84_0000 (localappdata) | Unhandled Except | B | UE4SS!RC::Unreal::FString::operator=() [D:\a\RE-UE4SS\RE-UE4SS\deps\fi | 31 |  | 1 | (no run folder) |
| 10-10 03:20 | REAL:F63CC90_0000 (localappdata) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 32 |  | 0 | (no run folder) |
| 10-10 02:54 | REAL:30161B5_0000 (localappdata) | 70 | B | UE4SS!RC::LuaType::push_nameproperty() [D:\a\RE-UE4SS\RE-UE4SS\UE4SS\s | 31 |  | 0 | (no run folder) |
| 10-10 02:52 | REAL:620C183_0000 (localappdata) | 10 | B | UE4SS!RC::LuaType::TLuaStringBase<RC::Unreal::FString,RC::LuaType::FSt | 176 |  | 0 | (no run folder) |
| 10-10 02:48 | REAL:35D9E2E_0000 (localappdata) | Unhandled Except | B | UE4SS!RC::Unreal::FString::operator=() [D:\a\RE-UE4SS\RE-UE4SS\deps\fi | 30 |  | 0 | (no run folder) |
| 10-09 22:23 | REAL:0794D2C_0000 (localappdata) | Unhandled Except | B | UE4SS!RC::LuaMadeSimple::Lua::get_string() [D:\a\RE-UE4SS\RE-UE4SS\dep | 58 |  | 0 | (no run folder) |
| 09-27 16:48 | REAL:B8A1030_0000 (localappdata) | 340 | C | ManorLords_Win64_Shipping | 6782 |  | 0 | (no run folder) |
| 10-15 16:37 | REAL:9918A38_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-14 12:42 | REAL:5010D8E_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-14 12:41 | REAL:E25FD19_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-14 12:39 | REAL:28DC4E3_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-13 20:06 | REAL:8E30235_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-13 20:03 | REAL:6A57BEE_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-13 20:02 | REAL:1E56595_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| 10-13 20:01 | REAL:6DFEDB8_0000 (localappdata) | LowLevelFatalErr | E | ManorLords_Win64_Shipping | 0 |  | 0 | (no run folder) |
| ? | m03-bisect-off-1 (M03-raid_behavior-01) | a | D | ? | 350 |  |  | [HarnessCommands] InvasionMod request 0038 InvasionMod.raid_behavior_state ok=true |

## Patterns in the table

- Stack thread: in 96 of the 143 reports the call stack has `engine_tick_hook`, then `process_simple_actions`, then `call_function`. This is the UE4SS game-thread queue (`ExecuteInGameThread` and similar). So the faulting Lua code runs on the game thread. Only 2 reports (group F, `20261017-234946-d78a` and `20261017-235133-4f64`) fault on a `LoopAsync` thread (`std::thread` then `update_async` then `process_delayed_actions` then `call_function`): a Lua error in a `LoopAsync` callback ended in an abort. (A Lua heap that was damaged by another thread still faults later on the game thread.)
- 88 of 117 reports with a log have the crash within 3 s of the last non-bridge log line. The last line is mostly a `HarnessActions` (37) or `HarnessCommands` (23) line, then `HarnessLogTest` (16), `InvasionMod.bandits` (13) and `InvasionMod.raid_behavior` (10). The crash is therefore usually during or right after a harness command or bridge request, not in the middle of a quiet fast-forward.
- Since 2026-10-22: last tags `HarnessCommands` 6, `InvasionMod.bandits` 4, `InvasionMod.vassals` 2, `HarnessLogTest` 2, `HarnessActions` 1, `scenario_settings` 1, `invasion` 1.
- Group A addresses are garbage (`0xffffffffffffffff`, `0x1ed87797829`, `0x25e55dc06e1`), and several crashes sit in table code (`getgeneric`, `luaH_next`). This points to a damaged Lua heap or table, not to one stale UObject.
- Both banditcamp crashes (`20261024-024700-6523`, `20261024-021558-0d65`) and `levels-first-raid-6` follow a `BANDITS` log line within 1 to 5 s. The bandits feature writes the region `publicOrder` every tick and logs "game rewrote order".
