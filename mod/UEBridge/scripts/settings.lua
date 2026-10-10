-- UEBridge settings. Every key is optional; a missing key takes the default shown.
-- This file belongs next to main.lua, inside the mod's scripts folder. That copy always wins; a
-- settings.lua at the mod root (where 1.0.0 put it) is read only when scripts\ has none.
-- Edit, save, then `ue4ss-bridge reload` (or the reload_mod tool), or restart the game.
return {
    -- false turns the bridge off without removing the mod. Nothing is polled.
    enabled = true,

    -- How often the request file is checked, in milliseconds.
    poll_ms = 50,

    -- false refuses raw Lua (the eval_lua tool). The structured tools (inspect_object,
    -- get_property, find_objects, ...) keep working through the batch op.
    -- Forced off when allow_writes = false (eval can write).
    allow_eval = true,

    -- false makes the bridge read-only: set_property, call_function, console_command,
    -- hook_function and eval_lua are refused. Reads are unaffected.
    allow_writes = true,

    -- Absolute path for request.json / response.json. Default: <game>\Binaries\Win64\ue4ss\bridge
    -- bridge_dir = "C:\\path\\to\\bridge",
}
