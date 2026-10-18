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
A capability path SHALL start with `harness/`, `mod/` or `process/`. A `mod/<feature>` path SHALL use the feature folder name from `mod/InvasionMod/Scripts/features/<feature>/`, or `mod/core` for the shared parts of the Invasion Mod. Player behavior SHALL be specified only as part of the Invasion Mod; the earlier standalone test mods have no capability.

#### Scenario: A new mod feature capability
- **WHEN** a change adds the first requirement for the Invasion Mod feature `invasion`
- **THEN** its delta spec path is `specs/mod/invasion/spec.md`
- Checked by review.

#### Scenario: The shared parts of the Invasion Mod
- **WHEN** a change adds requirements for the feature loader or the scheduler
- **THEN** its delta spec path is `specs/mod/core/spec.md`
- Checked by review.

#### Scenario: A path outside the groups
- **WHEN** a change uses a capability path such as `specs/raids/spec.md` or `specs/mods/policy-menu/spec.md`
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
Each spec scenario for harness or mod behavior SHALL name the check that covers it, as "Checked by `<path>`": a test scenario, or a Python test file in `harness/tests/` for behavior that runs without the game. A spec scenario for a process rule SHALL say "Checked by review" or name the command that checks it. A spec scenario with no check yet SHALL say "Not checked yet". A THEN step for game behavior SHALL state a range, not an exact value.

#### Scenario: A mod spec scenario
- **WHEN** a delta spec adds a requirement for raid timing
- **THEN** each of its spec scenarios has a line such as "Checked by `mod/InvasionMod/scenarios/invasion/first_raid.py`"
- **AND** its THEN steps state ranges such as "between day 30 and day 90"
- Checked by review.

#### Scenario: A harness spec scenario checked without the game
- **WHEN** a delta spec adds a requirement for the run launcher
- **THEN** its spec scenario may name a Python test, such as "Checked by `harness/tests/test_runlib_summary.py`"
- Checked by review.

#### Scenario: Behavior without a check
- **WHEN** a requirement describes built behavior that no test scenario or Python test covers
- **THEN** its spec scenario says "Not checked yet"
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
A change with something to build SHALL pass two pull requests. The spec pull request SHALL hold only the change folder (proposal, delta specs, design, tasks) and no archive. The implementation pull request SHALL hold the code, tests, test results, evidence and checked tasks, and SHALL end with the archive commit before it is submitted for review, so it shows the final state. A change with nothing to build (process rules, docs) SHALL use one pull request that holds the change and its archive.

#### Scenario: A finished change
- **WHEN** all tasks of a change are done and the full tests pass
- **THEN** the change is archived as the last commit of its implementation pull request, before that pull request is submitted for review
- **AND** after the merge, `openspec list` on `main` no longer shows the change
- Checked by `openspec list`.

#### Scenario: The spec pull request is merged
- **WHEN** the user approves and merges a spec pull request
- **THEN** the change is open in `openspec/changes/` on `main`, and the living specs are not changed yet
- **AND** `openspec list` on `main` shows the change as approved work that is not built
- Checked by `openspec list`.

#### Scenario: A change with nothing to build
- **WHEN** a change only changes process rules or docs
- **THEN** one pull request holds the change folder and the archive commit
- Checked by review.

### Requirement: Each change has one branch and one issue
Each change SHALL have one GitHub issue titled `Change: <change-name>`. Its spec pull request SHALL use the branch `spec/<change-name>`, and its implementation pull request SHALL use `feat/<change-name>` (or `fix/`, `docs/`, `chore/`), made from `main` after the spec pull request is merged. The issue body SHALL link the change folder and the branches.

#### Scenario: A new change is proposed
- **WHEN** a change folder is created
- **THEN** a GitHub issue `Change: <change-name>` exists with the `status: in progress` label
- **AND** the proposal links the issue
- Checked by review.

#### Scenario: The implementation branch
- **WHEN** the spec pull request of `add-great-raid-clock` is merged
- **THEN** the implementation starts on `feat/add-great-raid-clock`, made from the updated `main`
- Checked by review.

### Requirement: Legacy spec folders are read-only
The old legacy specs (formerly `docs/harness/<NN>-*/`, `docs/mod/M<NN>-*/` and `docs/mod/feature-breakdown.md`) SHALL live unchanged in `openspec/changes/archive/<date>-legacy-*/` as read-only history. No work SHALL happen in them. All their open work SHALL be an OpenSpec change. References SHALL use the archive paths; only `CHANGELOG.md` files keep old paths as history. The coverage data SHALL live in `openspec/specs/harness/coverage/`.

#### Scenario: A criterion is verified
- **WHEN** a criterion of the Invasion Mode brief is verified
- **THEN** `openspec/specs/harness/coverage/criteria.json` and `criteria.md` are updated
- **AND** `harness/tools/coverage.py --check-spec` passes
- Checked by `harness/tools/coverage.py --check-spec`.

#### Scenario: New work for an area with a legacy spec
- **WHEN** new work touches an area that has a legacy spec
- **THEN** the work is an OpenSpec change, and the archived legacy spec is only read as source material
- **AND** the change names the archived legacy file it continues
- Checked by review.

#### Scenario: Open legacy work
- **WHEN** an iteration such as M12.02 was still open in its legacy folder on 2026-10-18
- **THEN** it continues as its OpenSpec change, under the issue that the change names
- **AND** its archived legacy folder gets no more edits
- Checked by review.

#### Scenario: A link to a legacy note
- **WHEN** code, a skill, the wiki or a spec points to a legacy note
- **THEN** the path starts with `openspec/changes/archive/` and the file exists
- Checked by review and `wiki.py check` (for wiki sources).

### Requirement: The game design stays with the user
`design/` SHALL stay outside `openspec/`. A change SHALL only read it as source material, unless the user asks for a design change.

#### Scenario: A change uses a design rule
- **WHEN** a mod change needs a player rule from the design
- **THEN** the proposal cites the M00 section
- **AND** M00 is not changed by the change
- Checked by review.

### Requirement: A change names its issue
A change SHALL name its issue in the proposal, in the key `x-issue` of its `.openspec.yaml`, and in a comment `<!-- Issue: #<n> -->` under the first section heading of each delta spec. A line above the first heading SHALL NOT be used, because `openspec validate --strict` rejects it.

#### Scenario: A delta spec names its issue
- **WHEN** a delta spec is written for change issue #123
- **THEN** the file has the comment `<!-- Issue: #123 -->` under its first section heading, and `.openspec.yaml` has `x-issue: 123`
- **AND** `openspec validate <change-name> --strict` passes, and the archive does not copy the comment into the living spec
- Checked by review.

### Requirement: Gate 1 is the user's approval of the spec
A spec pull request SHALL be merged only after the user approves it on GitHub. An agent SHALL NOT merge it and SHALL NOT start the implementation before the merge. Review findings SHALL be fixed in the spec pull request with new commits.

#### Scenario: The user asks for a spec fix
- **WHEN** the user asks to change a requirement in a spec pull request
- **THEN** the agent fixes the delta spec on the same branch with a new commit
- **AND** no code exists yet that must change with it
- Checked by review.

### Requirement: Gate 2 is the user's approval of the test evidence
An implementation pull request SHALL be merged only after the user approves its test results and evidence on GitHub. An agent SHALL NOT merge it. If the implementation changes a delta spec, the pull request SHALL say so in a "Spec changes" section, and the user reviews that diff in the same gate.

#### Scenario: A spike changes the plan
- **WHEN** a spike during the implementation shows that a requirement cannot hold
- **THEN** the implementation pull request changes the delta spec and names the change under "Spec changes"
- Checked by review.

#### Scenario: A pull request without a gate
- **WHEN** a pull request has no change folder, no spec change and no acceptance from test results (for example a typo fix in the wiki)
- **THEN** an agent may merge it after the full tests pass
- Checked by review.

### Requirement: Pull requests stay light
A pull request body SHALL have the sections Summary, Spec changes, Test results, Evidence and Not verified. Test results SHALL be a short table: the check (test scenario, Python test or command), the run id or test file, the verdict, and the key number or range. The body SHALL NOT hold raw logs. A section with nothing to report SHALL say "None".

#### Scenario: A mod iteration with real-game runs
- **WHEN** an implementation pull request claims that its acceptance criteria pass in the real game
- **THEN** its "Test results" table lists each criterion with its test scenario, run id, verdict and measured range
- Checked by review.

### Requirement: Visual results need picture evidence
An implementation pull request SHALL include picture evidence when its result is visual: UI features (menus, widgets, banners, letters and other text on screen), 3D models, materials and textures, building placement and geometry, units in the world (models, equipment, banners), and world results the player sees (for example ruins, camps, construction sites). Other changes MAY include pictures. Numeric rules SHALL be proven by test results, not by pictures.

#### Scenario: A new menu
- **WHEN** a change adds or changes a mod menu
- **THEN** its implementation pull request shows at least one picture of the menu in the real game
- Checked by review.

#### Scenario: A new building part
- **WHEN** a change adds a mesh or places a building part
- **THEN** its implementation pull request shows the part in the game from a view where position, size and material can be judged
- Checked by review.

#### Scenario: A tribute formula
- **WHEN** a change only changes a numeric rule such as a tribute share
- **THEN** no picture is required, and the test results prove the rule
- Checked by review.

### Requirement: Evidence lives in the change
Picture evidence SHALL be committed in plain git to `openspec/changes/<change-name>/evidence/`, compressed, at most the game window size (1280x720), and about 1 MB per change in total. Each picture SHALL be listed in `evidence/README.md` with its test scenario and run id. The pull request SHALL embed the pictures with links that contain the commit SHA, so the links stay valid after the archive and the merge.

#### Scenario: Evidence after the archive
- **WHEN** a change with evidence is archived
- **THEN** the pictures are in `openspec/changes/archive/YYYY-MM-DD-<change-name>/evidence/` with their `README.md`
- **AND** relative links inside the change still resolve
- Checked by review.

#### Scenario: Evidence that is too large
- **WHEN** the evidence of a change is much larger than 1 MB
- **THEN** the pictures are compressed or cut to the relevant area before the commit
- Checked by review.
