# HarnessTelemetry in the real game

Date: 2026-10-10. Runs made by the launcher with the default interval of 5 s.

## Result: the Lua mod worked unchanged
No change to `HarnessTelemetry.lua` or to its 19 mock tests was needed.
- `mod.log` has `[Telemetry] sampling every 5 s into <run>/telemetry.jsonl` in each run. `deploy.ps1` enabled the mod.
- Each sample has all fields (`t`, `clock`, `paused`, `date.day/month/year/season`, `player.silver/influence/kingsFavour`, 7 regions with
  `name`, `settled`, `approval`, `publicOrder`, `wealth`, `food`, `population`, `homeless`). `errors` was empty in every sample checked.
  `paused` is null in the first sample only.
- Spacing: every gap in `telemetry-sanity` runs was 5 s (`t` has a resolution of 1 s). The scenario allows 3 to 7 s.
- The first samples exist before `READY` (the game map is loaded at clock 0 while HarnessBoot works). A run has about 8 samples at the end of `time-advance`
  and 16 at the end of `telemetry-sanity`.
- The sampler does not slow the game: at speed 1 the clock rate over 40 s was 1.001 game s per wall s. Boot took 30 to 32 s, the same as before (spec 03: 30 to 32 s). The 2 pauses of HarnessBoot are unchanged (`pause_calls` 2).
- Sampling works while paused (samples with `paused: true`, same clock).
- Values at the start of the test save: silver, influence and kingsFavour are 0. Seven regions. Three are settled (Hochweg, Riesenbuckel, Rangbachau):
  approval 50, publicOrder 100, wealth 50, population 10, homeless 5. The others are all 0 except approval 50 and publicOrder 100.
- Region names are the `regionName` text ("Hochweg"), not the object names (`Goldhof`). The Lua mod and the Python snapshot give the same names.

## Python side
- `snapshot()` reads the same fields through the bridge (one `get` for the region list gives object references). In `telemetry-sanity` the snapshot
  taken after the pause equals the last telemetry sample (taken after the pause) (date, player, region name, settled, population).
- A snapshot costs about 70 bridge calls (7 regions, 8 reads each).

## Problems found while testing (not in the Lua)
- `changeGameSpeed` after the boot pause drops back to 1x (see `time-measurements.md`). This was found through the first `time-advance` run, which timed out at 8x with the clock running at 1x.
  The telemetry samples of that run showed the clock rate (`clock` +5 per 5 s) and made the cause clear.
- Telemetry is wall-time based, so a scenario that runs at 8x for 3 s gets no sample. `telemetry-sanity` runs 40 game seconds at speed 1 for this reason.

## Not verified
- Cost of sampling with a large village (the test save is small).
- A sample at the moment of a save load or a map change. Only one map was used.
- `HarnessTelemetry.register` with a real metric in the real game (tested with the fake only).
