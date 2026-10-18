# process/spec-workflow Specification

## Purpose
Defines how this repo plans, records and closes work: living specs, one OpenSpec change per piece of work, notes, the archive, and the branch and issue that go with each change.

## Requirements

### Requirement: Living specs hold the current behavior
The repo SHALL keep one living spec per capability at `openspec/specs/<capability-path>/spec.md`. A living spec SHALL describe only the behavior that is true on `main`. It SHALL NOT hold status logs, plans or spike results.

#### Scenario: A reader looks up the current behavior
- **WHEN** a reader opens `openspec/specs/<capability-path>/spec.md`
- **THEN** every requirement in it is true on `main`
- **AND** the file has no dated status lines and no open plans
- Checked by review.

### Requirement: Capabilities use three groups
A capability path SHALL start with `harness/`, `mod/` or `process/`. A `mod/<feature>` path SHALL use the feature folder name from `mod/InvasionMod/Scripts/features/<feature>/`.

#### Scenario: A new mod feature capability
- **WHEN** a change adds the first requirement for the Invasion Mod feature `invasion`
- **THEN** its delta spec path is `specs/mod/invasion/spec.md`
- Checked by review.

#### Scenario: A path outside the groups
- **WHEN** a change uses a capability path such as `specs/raids/spec.md`
- **THEN** the review rejects the change until the path starts with `harness/`, `mod/` or `process/`
- Checked by review.

### Requirement: New work starts as a change
Every new harness feature, mod feature, mod iteration and spike SHALL start as a change folder `openspec/changes/<change-name>/` before code is written. `<change-name>` SHALL be kebab-case and start with a verb.

#### Scenario: A new mod iteration
- **WHEN** the next iteration of a mod feature is planned
- **THEN** a change such as `openspec/changes/add-great-raid-clock/` exists with a proposal before any mod code changes
- Checked by review.

#### Scenario: A tuning-only change
- **WHEN** only values in a feature `config.lua` change
- **THEN** no change folder is needed
- **AND** the values are logged in the feature feedback file and in the mod changelog
- Checked by review.

### Requirement: Changes validate before review
A change SHALL pass `openspec validate <change-name>` before its pull request is opened for review.

#### Scenario: A change with a broken spec scenario
- **WHEN** a delta spec has a requirement without a `#### Scenario:` block
- **THEN** `openspec validate <change-name>` reports an error
- **AND** the pull request is not opened until the error is fixed
- Checked by `openspec validate`.

### Requirement: Spec scenarios name their test scenario
Each spec scenario for harness or mod behavior SHALL name the test scenario that checks it, as "Checked by `<path>`". A spec scenario for a process rule SHALL say "Checked by review" or name the command that checks it. A THEN step for game behavior SHALL state a range, not an exact value.

#### Scenario: A mod spec scenario
- **WHEN** a delta spec adds a requirement for raid timing
- **THEN** each of its spec scenarios has a line such as "Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`"
- **AND** its THEN steps state ranges such as "between day 30 and day 90"
- Checked by review.

### Requirement: Findings live in the change
Spike findings and implementation notes SHALL be written to `openspec/changes/<change-name>/notes/<topic>.md`, one file per topic. Notes SHALL NOT be kept only in chat.

#### Scenario: A spike finds an engine fact
- **WHEN** a spike inside a change finds what a game function does
- **THEN** the finding is in a `notes/<topic>.md` file of that change, with the question, method, numbers and verdict
- Checked by review.

### Requirement: Lasting engine facts move into the wiki
Before a change is archived, each engine fact in its `notes/` that stays true SHALL be added to the wiki in `docs/wiki/`. The full notes SHALL stay in the archived change.

#### Scenario: Archive of a change with notes
- **WHEN** a change with a `notes/` folder is archived
- **THEN** the wiki page for that area states the lasting facts and links the archived note
- Checked by review.

### Requirement: A change is archived in its own pull request
A change SHALL be archived with `openspec archive <change-name>` as the last commit of its pull request, before the merge. The archive SHALL merge the delta specs into `openspec/specs/` and move the folder to `openspec/changes/archive/YYYY-MM-DD-<change-name>/`.

#### Scenario: A finished change
- **WHEN** all tasks of a change are done and the full tests pass
- **THEN** the last commit of the pull request archives the change
- **AND** after the merge, `openspec list` on `main` no longer shows the change
- Checked by `openspec list`.

### Requirement: Each change has one branch and one issue
Each change SHALL have one branch `feat/<change-name>` (or `fix/`, `docs/`, `chore/` for those types) and one GitHub issue titled `Change: <change-name>`. The issue body SHALL link the change folder and the branch.

#### Scenario: A new change is proposed
- **WHEN** a change folder is created
- **THEN** a GitHub issue `Change: <change-name>` exists with the `status: in progress` label
- **AND** the proposal links the issue
- Checked by review.

### Requirement: Legacy spec folders are read-only
`docs/harness/` and `docs/mod/` SHALL NOT get new spec folders, new iteration files or new notes, with one exception. Work that has an open issue under a legacy spec on the day of this change MAY finish in its legacy folder. Legacy folders SHALL NOT be moved or renamed. The coverage data of spec 10 (`criteria.json` and the criteria tables of its README) SHALL stay live, because the coverage tool reads them.

#### Scenario: A criterion is verified
- **WHEN** a criterion of the Invasion Mode brief is verified
- **THEN** `criteria.json` and the spec 10 README tables are updated
- **AND** `harness/tools/coverage.py --check-spec` passes
- Checked by `harness/tools/coverage.py --check-spec`.

#### Scenario: New work for an area with a legacy spec
- **WHEN** new work touches an area that has only a legacy spec
- **THEN** the work starts as an OpenSpec change
- **AND** its delta spec seeds the living spec from the "current state" of the legacy README
- Checked by review.

#### Scenario: Open legacy work
- **WHEN** an iteration such as M12.02 was already open in its legacy folder before this change
- **THEN** it may finish and close in that legacy folder
- Checked by review.

### Requirement: The game design stays with the user
`docs/mod/M00-invasion-mod/` SHALL stay outside `openspec/`. A change SHALL only read it as source material, unless the user asks for a design change.

#### Scenario: A change uses a design rule
- **WHEN** a mod change needs a player rule from the design
- **THEN** the proposal cites the M00 section
- **AND** M00 is not changed by the change
- Checked by review.
