# Proposal: backfill living specs

Issue: #253. Branch: `feat/backfill-living-specs`.

## Why

After `adopt-openspec`, `openspec/specs/` holds only the process rules. The behavior of the harness and the Invasion Mod is still described only in 48 legacy specs, mixed with status logs and plans. The user asked (2026-10-18) to rewrite all of them into OpenSpec form now, instead of one capability at a time. The legacy specs stay.

## What Changes

- Add one living spec for each capability with built behavior: 28 harness capabilities and 15 Invasion Mod capabilities. The capability map is in `design.md` (D1).
- Each requirement states built behavior on `main`, with spec scenarios that name their check.
- Copy the open items of each legacy mod `feedback.md` to `openspec/specs/mod/<feature>/feedback.md`.
- Change two process rules: one more capability group (`mod/core`), and checks may be Python tests or "Not checked yet".
- This reverses decision D4 of `adopt-openspec` ("seed on first touch") at the user's request. The rule that the first change seeds a living spec still holds for capabilities that are not in the map.

## Non-goals

- No deletion, move or rename of legacy specs, notes or iteration files.
- No code change.
- No engine facts or spike numbers in requirements. They stay in legacy notes and the wiki.
- Planned iterations are not converted into changes in this change (D6 in `design.md`).
- No change to `design/`.

## Legacy folders

All of `docs/harness/` and `docs/mod/M01` to `M14`, as listed in `design.md` D1.

## Capabilities

### New Capabilities
All capabilities in the D1 table of `design.md`, under `harness/`, `process/testing-strategy` and `mod/`.

### Modified Capabilities
- `process/spec-workflow`: the `mod/core` group, no standalone mods, and the rule for checks.

## Impact

- New: `openspec/specs/**` (through the archive), `openspec/specs/mod/<feature>/feedback.md`.
- Changed: `docs/harness/README.md`, `design/mod/README.md` (legacy banners now point to the living specs), the wiki page `docs/wiki/operations/docs-and-specs.md`, `CHANGELOG.md`.
