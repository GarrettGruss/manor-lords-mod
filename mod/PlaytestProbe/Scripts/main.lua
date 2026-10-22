-- PlaytestProbe: harness-only probe mod for spike-playtest-telemetry (#384). Not shipped.
local commands = require("HarnessCommands")
local probe = require("HarnessTelemetryProbe")
local log = require("HarnessLog")

local P = "PlaytestProbe."
local function reg(name, fn, schema) commands.register(P .. name, fn, schema or {}) end
local PATH = { type = "string", required = true, maxLength = 120 }

reg("log_start", function() return probe.log_start() end)
reg("burst", function(a) return probe.burst(a.n) end, { n = { type = "integer", required = true, min = 1, max = 100000 } })
reg("status", function() return probe.status() end)
reg("clean_exit", function() return probe.clean_exit() end)
reg("detect_previous", function() return probe.detect_previous() end)
reg("gc_sentinel", function() return probe.gc_sentinel() end)
reg("quit_hooks", function() return probe.quit_hooks() end)
reg("newest_crash", function() return probe.newest_crash() end)
reg("read_test", function(a) return probe.read_test(a.rel) end, { rel = PATH })
reg("write_report_folder", function() return probe.write_report_folder() end)
reg("zip_start", function(a)
    return probe.zip_start(a.out, {
        { name = "save/saveGame_probe.sav", path = a.save },
        { name = "session.log", path = a.log },
        { name = "report.json", path = a.report } }, a.step_kb)
end, { out = PATH, save = PATH, log = PATH, report = PATH, step_kb = { type = "integer", required = true, min = 0, max = 4096 } })
reg("zip_status", function() return probe.zip_status() end)
log.say("PlaytestProbe", "loaded, base " .. probe.base)
reg("menu_open", function(a) return probe.menu_open(a.checked == 1) end, { checked = { type = "integer", required = true, min = 0, max = 1 } })
reg("menu_close", function() return probe.menu_close() end)
reg("menu_set_text", function(a) return probe.menu_set_text(a.text) end, { text = { type = "string", required = true, maxLength = 200 } })
reg("menu_set_checked", function(a) return probe.menu_set_checked(a.on == 1) end, { on = { type = "integer", required = true, min = 0, max = 1 } })
reg("menu_focus", function() return probe.menu_focus() end)
reg("menu_state", function() return probe.menu_state() end)
