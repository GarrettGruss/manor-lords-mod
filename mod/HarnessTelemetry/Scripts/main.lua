-- HarnessTelemetry mod: starts the telemetry sampler (see shared/HarnessTelemetry/HarnessTelemetry.lua).
-- The sampler is in a shared module, so other mods can call HarnessTelemetry.register(...).
-- HARNESS_TELEMETRY_UNITS=1 adds custom.units to each sample: unit counts by side and the loot totals (spec 10, about 10 ms a sample).
local VERSION = "2"
require("HarnessLog").info("HarnessTelemetry", "loaded version " .. VERSION)
local telemetry = require("HarnessTelemetry")
if os.getenv("HARNESS_TELEMETRY_UNITS") == "1" then
    require("HarnessUnits").register_telemetry(telemetry)
end
telemetry.start()
