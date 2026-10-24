## Why

Issue: #455. The button "Request arms shipment" on the liege screen (change add-scenario-start-kit) refuses on click when no manor is built. The player sees an active button that does nothing. The owner decided (2026-10-23): the button SHALL be disabled while no manor is built, with the reason "Build a manor first" shown under it, and a click does nothing.

## What Changes

- The liege menu reads the manor state and adds the reason "Build a manor first" to the arms button rule. The reason shows in the line under the button text (the arms info text), not in the label.
- The button gets a disabled look: a grey tint of the click button (`SetColorAndOpacity`, as the tech tree widget does) and clicks are ignored while it is disabled.
- The same look is used for the cooldown and the not-enough-silver cases. The label stays "Request arms shipment" in all cases.
- Lua only: no pak change is expected. `SetIsEnabled` is not used (a Lua error inside a UObject call can crash UE4SS). The final choice is recorded in `notes/disabled-look.md`.

## Impact

- Spec: `mod/liege_influence` (MODIFIED requirements: the arms button and the cooldown).
- Code: `mod/InvasionMod/Scripts/features/liege_influence/init.lua`, fake game tests, test scenario `arms_shipment.py`.
