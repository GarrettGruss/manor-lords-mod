## Why

Liege contracts tier III will cost the player a loan of army units or peasants for a time (owner decision 2026-11-04). If a loan is impossible, the units are lost. The mod needs to know what a script can take away and give back. Issue: #568.

## Questions

1. Can the mod take a player squad (retinue or militia) away for N game days and give it back (hide and disable, transfer, or remove and respawn)?
2. Can the mod take villagers away for N game days and give them back, or only remove and re-add them?
3. What is lost with the "lose the units" fallback, and is it safe?

For each method: does it work, is it safe (no crash), does it survive a save and load (reasoning or the ModState pattern; no save call).

## What Changes

- Spike with a probe module (`mod/shared/HarnessLoanProbe`, command `loan_probe`) and a hidden probe test scenario (`harness/scenarios/probe_loan_units.py`), run in slot 1.
- Notes in `notes/`, lasting facts in the wiki.

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None.

## Impact

Probe code and notes. No change to a living spec.
