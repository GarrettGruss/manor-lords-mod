# Proposal: archive the legacy specs

Issue: #288. Branch: `docs/archive-legacy-specs` (single pull request; it also carries `move-coverage-criteria-to-openspec`, #279).

## Why

After `migrate-legacy-work`, the legacy specs hold no open work. But their 245 implementation notes hold knowledge that is not elsewhere (spike results, measured numbers, crash findings, screenshots, probe scripts), so they cannot be deleted. The user accepted on 2026-10-18 to move them into the OpenSpec archive instead. This keeps all knowledge, matches the archive idea (done work with its full context), and removes the legacy folders.

## What Changes

- Move each legacy folder unchanged inside to `openspec/changes/archive/<date>-legacy-<NN>-<name>/` (harness) or `<date>-legacy-m<NN>-<feature>/` (mod). `<date>` is the day the folder was first added in git. The batch plan `docs/mod/feature-breakdown.md` becomes `<date>-legacy-mod-feature-breakdown/README.md`. 49 entries, 337 files.
- Remove `docs/harness/README.md`. Rewrite `docs/mod/README.md` for the design only. `docs/mod/M00-invasion-mod/` (the user's design) stays.
- Rewrite every reference in 160 files: plain paths, `repo://` wiki sources, relative Markdown links (also inside the moved files), and relative paths in backticks inside the moved files. `CHANGELOG.md` files keep the old paths as history. The map is `notes/path-map.md`.
- `process/spec-workflow`: the legacy requirement names the archive location.
- Update CONTRIBUTING.md, `openspec/config.yaml`, the skills and the wiki.

## Non-goals

- No edit of the content of the moved files beyond their links and paths.
- No harvest of engine facts into the wiki (a later cleanup).
- No change to `docs/mod/M00-invasion-mod/`.

## Legacy folders

All of them; this change moves them.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `process/spec-workflow`: where the legacy specs live.

## Impact

- Moved: 337 files. Edited: 160 files (comments, docstrings, skills, wiki, specs, open changes). Removed: `docs/harness/README.md`.
- No code behavior changes. Test results are the same as on `main`.
