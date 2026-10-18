# M13 iteration 02: retinue-capacity

Branch: `feat/M13-manor_stronghold-02-retinue-capacity` (stacked on iteration 01, PR #210). Issue: see PR.

## Goal
A tech tree upgrade raises the retinue limit of the manor. Spike question (M00 open question 16): does a raised limit change real hires?

## Changes
- Tree effect kind `retinue_capacity` (add). `veteran_levies` (Oppression) and `militia_rights` (Prosperity) give +12 (TBD).
- `manor_stronghold/retinue.lua`: post-hooks on `SMBuildingMaster:getModularGarrisonLimit` (adds the bonus for manor modules) and `canHireRetinue` (true while the bound retinue is below the raised limit).
- Commands `retinue_state` and `retinue_hire` (calls `hireExtraRetinue`).
- Probe `probe-retinue-cap` (harness, hidden) for the spike.

## Acceptance criteria
- R1: base limit 12; hiring stops at 12 (`canHireRetinue` false).
- R2: after Militia Rights the limit reads 24 and the hire gate is open.
- R3: real hires: measured, see Result.

## Result
Spike result (negative for real hires). Runs `20261018-092054-f458` (no bonus) and `20261018-093531-4be8` (bonus 24 through the old garrison hook): the script limit reads 36, but `hireExtraRetinue` stops at 12 bound men in both. With the new `canHireRetinue` hook the gate is true, and `hireExtraRetinue` still adds no man above 12 (run `20261018-094006-4a4f`). So the native hire code enforces its own limit (12, 24 with a keep). The mod changes what script callers and the Blueprint retinue editor read, not the native hire.
Scenario `manor-stronghold-retinue` passes (R1, R2, and R3 as a known characterization): runs `20261018-094356-cc6c`, `20261018-094719-50f3`.
Open: a mod-owned hire path (extra retinue squads with `InitializeEmptyRetinueSquad`, or the retinue editor button) is not tried. The editor button needs the real mouse.
Notes: `../implementation-notes/iteration-02-retinue-capacity.md`.
