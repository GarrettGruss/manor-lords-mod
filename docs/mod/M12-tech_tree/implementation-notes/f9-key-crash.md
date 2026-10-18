# F9 key hang of the tech tree menu (#245)

## Symptom
A real F9 press in a kept-open session froze the game. No menu, the bridge never answered.

## Reproduction
Scenario `tech-tree-widget-key` (new) presses the real F9 key without opening the menu by command.
Run 20261018-154053-d9be: the game crashed 0.3 s after the key press with EXCEPTION_ACCESS_VIOLATION.
Call stack: `luaH_getint` <- `lua_rawgeti` <- `UObjectBase::construct` <- `auto_construct_object` (a Lua global function such as FindFirstOf).
The user saw a hang of the same fault (corrupt Lua state).

## Cause
`RegisterKeyBind` callbacks run on the input thread, not the game thread. The old callback called Lua there (`core.log`-free, but it entered the shared Lua state and queued `ExecuteInGameThread`) while the game thread ran scheduler jobs in the same Lua state. This is the same race as the LoopAsync corruption in PR #166. The earlier scenarios opened the menu by command, so the key path was never tested. The raid widget (F8) has the same code. It passed by luck of timing.

## Fix
The key callback only sets a Lua boolean (`toggle_requested`). The scheduler tick (game thread) reads the flag and calls `toggle`. Applied to `tech_tree_widget` and `raid_widget`. No pak change.

## Results
Runs of `tech-tree-widget-key` after the fix: 20261018-154213-0a49 pass, 20261018-154331-093d pass.
The third run and the F8 run were refused by the run cap (400 runs, `runs/.iterations`). Open: third pass and a real F8 run (`invasion-raid-widget --pak raidmenu`).
