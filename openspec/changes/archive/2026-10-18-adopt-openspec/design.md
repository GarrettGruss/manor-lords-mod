# Design: adopt OpenSpec

## Context

See `proposal.md` for the motivation. The requirements are in `specs/process/spec-workflow/spec.md`.

Current state on the day of this change (2026-10-18):
- `docs/harness/` has 33 specs (00 to 33, no 20). `docs/mod/` has M00 to M14 and `feature-breakdown.md`.
- 15 issues are open. Most belong to legacy specs (for example spec 33, M12.02, spec 11).
- Code docstrings (about 12), skills, `CHANGELOG.md` and issues link to legacy paths.
- `harness/tools/coverage.py` reads `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/criteria.json`.
- `openspec init --tools claude` (CLI 1.14.3) made 6 skills in `.claude/skills/openspec-*/` and 6 commands in `.claude/commands/opsx/`.

## Goals / Non-Goals

**Goals:**
- One place for the current behavior, one place for open work and one place for history.
- Agents get the project rules in every OpenSpec artifact prompt, through `openspec/config.yaml`.
- No broken links and no tool changes.

**Non-Goals:**
- A converter for legacy specs.
- A coverage tool that reads `openspec/specs/`. That can be a later change.

## Decisions

### D1: Use the default `spec-driven` schema
The default artifacts (proposal, specs, design, tasks) fit our README parts (goal, criteria, plan). Notes are a project rule in `config.yaml`, not an artifact.
Alternative: fork a `harness` schema with a `notes` artifact. Rejected for now: schemas are marked experimental in the CLI, and `openspec update` keeps working without a fork.

### D2: Project rules go into `openspec/config.yaml`, not into the generated skills
`openspec update` rewrites `.claude/skills/openspec-*/` and `.claude/commands/opsx/`. Edits there would be lost. The `context`, `rules` and `operations` fields of `config.yaml` reach every artifact prompt.

### D3: Three capability groups
`harness/<name>`, `mod/<feature>`, `process/<name>`. This keeps the harness and the mod apart, as CLAUDE.md requires ("Harness code must not name the mod or its features"). The mod feature name matches the folder in `Scripts/features/`.

### D4: Seed living specs on first touch
A legacy README mixes state, logs and plans. Only the "current state" is a spec. The first change that touches a capability writes its requirements as ADDED, from the legacy README and the code. OpenSpec's own brownfield guide warns that a bulk back-fill goes stale.
Alternative: convert all 48 specs now. Rejected: high cost, and the result is not checked by real changes.

### D5: Legacy folders stay where they are
A move would break about 12 docstrings, the skills, the changelog and the issue links. Each legacy root gets a README that says "read-only legacy" and points to `openspec/`. Open legacy work may finish in place.

### D6: Archive inside the pull request
The user approved merges after the full tests pass. The pull request is the review point. The last commit runs `openspec archive <change-name> --yes`, so `main` never has a done change in `openspec/changes/`.
Alternative: archive after the merge on `main`. Rejected: it needs an extra commit on `main`, and CLAUDE.md keeps feature work off `main`.

### D7: Branch and issue names follow the change name
Branch `feat/<change-name>`. Issue `Change: <change-name>`. The archive date prefix gives the order, so the `<NN>` numbers stop for new work. Old issue titles stay.

### D8: Mod feature feedback stays per feature
Player feedback for a mod feature goes to `openspec/specs/mod/<feature>/feedback.md`, next to the living spec. A change that answers feedback links the line. The legacy `feedback.md` files stay where they are, and the first change for a feature moves their open items.

### D9: Terms "spec scenario" and "test scenario"
OpenSpec needs `#### Scenario:` headings. The harness already uses "scenario" for test files. The rules use "spec scenario" and "test scenario" so one term means one thing.

## Risks / Trade-offs

- [Risk] Two places to look during the move (legacy and `openspec/`). → `docs/harness/README.md`, `design/README.md` and the wiki page say which is which. CLAUDE.md states the rule.
- [Risk] The CLI is a second toolchain (Node). → Only validate and archive need it. Tests do not. The skills say how to install it.
- [Risk] Claude Code runs on Windows and in WSL. The CLI must be installed in each shell that runs it. → The wiki page names the install command.
- [Risk] OpenSpec sends anonymous usage stats by default. → The wiki page names the opt-out (`OPENSPEC_TELEMETRY=0` or `openspec config set telemetry.enabled false`). The user decides.
- [Risk] `openspec update` may change the generated skills. → They are generated files. Review their diff like any dependency update.
- [Risk] An extra file in `openspec/specs/mod/<feature>/` (D8) might confuse the CLI. → Task 1.3 checks that `openspec validate --all` accepts it.

## Migration Plan

1. Land this change: config, rules, legacy banners, skills, wiki.
2. The next mod iteration or harness feature is the first real change. It seeds its living spec.
3. Rollback: delete `openspec/`, the generated skills and commands, and revert CLAUDE.md. Legacy folders were not changed, so nothing else is lost.
