# Proposal: close the open items of composite buildings

Issue: #104. Legacy source: `openspec/changes/archive/2026-10-15-legacy-18-composite-buildings/README.md`. Legacy issues: #104 (open, "Spike: building access points and a 4-oxen stable"); #69 and #94 are closed.

## Why

Spec 18 proved that a pak can add a composite building and that a real click can place it. Some items stayed open:
- No build menu card (category, art, name text) exists for a new building id.
- The Siege Camp (row 483) cannot be built, because no call adds its master to a region.
- The 4-oxen stable (#104): capacity 4 and the two-shed look work, but there is no committed test scenario. Buying oxen adds only one. The owner stopped the hitch tests on 2026-10-15 because the hitch spots are native.

## What Changes

- Find how the build menu builds a card for a new id.
- Optional, if the owner wants it: find a region path for the Siege Camp.
- Add a test scenario for the large stable (row 125) that does not need `--keep-open`.
- Find why repeated oxen orders add only one ox.

## Non-goals

- Hitch spots for each ox (native code; owner decision of 2026-10-15, notes `big-ox-shed-test.md` and `ox-hitch-hook.md`).
- A finished content pak for release.
- Changing the manor module system.

## Legacy folders

- `openspec/changes/archive/2026-10-15-legacy-18-composite-buildings/` (notes: `access-points.md`, `real-mouse-placement-proof.md`, `siege-camp-build.md`, `hidden-buildings.md`, `siege-camp-and-bm.md`).

## Capabilities

### New Capabilities
- None. This is a spike (`skip_specs`).

### Modified Capabilities
- None. A delta spec for `harness/building-commands` is written if a menu card command is added.

## Impact

- Pak `mod/HarnessActions/paks/stable4_P.pak` and the tools `harness/tools/s104_stable.py`, `s94_drive.py`.
- New test scenario in `harness/scenarios/`.
