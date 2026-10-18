# Proposal: split the design brief

Issue: #292. Branch: `docs/split-design-brief` (single pull request, nothing to build).

## Why

After `archive-legacy-specs`, `docs/mod/` held only the M00 overview design and its companions. M00 mixed three jobs:
- the lasting philosophy that guides every mod spec;
- the decision log of the user;
- plans that go stale (feature map, build plan, balance targets, open questions), which the changes and living specs now hold.

On 2026-10-18 the user chose a top-level `design/` folder and accepted the split by job. OpenSpec treats such a document as source material, not as a spec, and puts what every planning request needs into `config.yaml` `context:` (OpenSpec docs: `existing-projects.md`, `migration-guide.md`).

## What Changes

- New `design/`, owned by the user:
  - `invasion-mod.md`: the philosophy sections of M00, word for word (vision, pillars, core loop, start state, factions, vassals, liege, raids, bandits, refugees, non-terminal defeat, leadership paths, pressure systems, pacing, out of scope).
  - `decisions.md`: the decision log, word for word, with its numbers kept, because 17 files cite "decision N".
  - `trailer.md`: moved.
  - `README.md`: what the folder is.
- **A deviation from the agreed split:** the decision log stays in `design/` rather than going to the archive, because the decisions are still in force and cited.
- The original M00 README (a full snapshot, with the feature map, build plan, balance targets and open questions) and the five feasibility reviews move to `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/`.
- The three M00 open questions that are not answered are added to the open change `decide-open-mod-rules` (rows 10 to 12).
- `openspec/config.yaml` gets a short summary of the vision, the pillars and what is out of scope, plus a proposal rule: a mod proposal names the design section or decision it serves and must not contradict a pillar.
- References are rewritten. Two reference-only fixes in the moved text:
  - "See Open questions" in `invasion-mod.md` now points to the change `add-plundered-start`.
  - "implementation-notes/feasibility-summary.md" in `decisions.md` now points to the archive.
- `docs/mod/` is removed.

## Non-goals

- No change to the design content.
- No move of the wiki (`docs/wiki/`).

## Legacy folders

`docs/mod/M00-invasion-mod/` (moved by this change).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `process/spec-workflow`: where the design lives, and how proposals use it.

## Impact

- New: `design/` (4 files). Archived: the M00 README and 5 feasibility reviews.
- Changed: references in 44 files, `openspec/config.yaml`, the wiki source map, `CHANGELOG.md`, the change `decide-open-mod-rules`.
