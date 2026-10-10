-- HarnessTelemetry mod: starts the telemetry sampler (see shared/HarnessTelemetry/HarnessTelemetry.lua).
-- The sampler is in a shared module, so other mods can call HarnessTelemetry.register(...).
local telemetry = require("HarnessTelemetry")
telemetry.start()
