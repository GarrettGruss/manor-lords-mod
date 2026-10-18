# Spec Delta

## MODIFIED Requirements

<!-- Issue: #264 -->

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
Each change SHALL have one GitHub issue titled `Change: <change-name>`. Its spec pull request SHALL use the branch `spec/<change-name>`, and its implementation pull request SHALL use `feat/<change-name>` (or `fix/`, `docs/`, `chore/`), made from `main` after the spec pull request is merged. The issue body SHALL link the change folder and the branches. The change SHALL name its issue in the proposal, in the key `x-issue` of its `.openspec.yaml`, and in a comment `<!-- Issue: #<n> -->` under the first section heading of each delta spec.

#### Scenario: A new change is proposed
- **WHEN** a change folder is created
- **THEN** a GitHub issue `Change: <change-name>` exists with the `status: in progress` label
- **AND** the proposal links the issue
- Checked by review.

#### Scenario: A delta spec names its issue
- **WHEN** a delta spec is written for change issue #264
- **THEN** the file has the comment `<!-- Issue: #264 -->` under its first section heading, and `.openspec.yaml` has `x-issue: 264`
- **AND** `openspec validate <change-name> --strict` passes, and the archive does not copy the comment into the living spec
- Checked by review.

#### Scenario: The implementation branch
- **WHEN** the spec pull request of `add-great-raid-clock` is merged
- **THEN** the implementation starts on `feat/add-great-raid-clock`, made from the updated `main`
- Checked by review.

## ADDED Requirements

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
