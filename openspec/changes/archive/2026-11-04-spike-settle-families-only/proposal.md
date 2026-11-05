## Why

The start kit adds families with `settleRegion`. Each call also makes a second tent camp, an ox and a small supply package (earlier spike, `notes/earlier-settle-extras-spike.md`). The owner accepted this on 2026-11-04. The owner thinks a pak data change could add a settle path that makes only families. This spike checks that idea. Issue: #560.

## What Changes

- Spike: search the game data for what drives `settleRegion`, and test the call in the real game (slot 1).
- Spec: record the accepted extras in `mod/scenario_settings` until a data-based fix exists.
- Wiki: record the engine facts.

## Capabilities

### Modified Capabilities
- `mod/scenario_settings`: the start kit settle call also adds a second tent camp, an ox and a small supply package (accepted).

## Impact

Docs and one probe test scenario (`harness/scenarios/probe_settle_families_only.py`). No mod code and no pak change.
