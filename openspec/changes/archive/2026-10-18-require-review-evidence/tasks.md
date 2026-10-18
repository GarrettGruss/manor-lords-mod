# Tasks

## 1. Spec

- [x] 1.1 Write the proposal and the delta for `process/spec-workflow` (two gates, issue references, light pull requests, picture evidence); verify with `openspec validate require-review-evidence --strict`
- [x] 1.2 Check that an issue reference in a delta spec passes `--strict` and is dropped by the archive (a comment inside a section and `x-issue` in `.openspec.yaml` pass; a line above the first heading fails); verify with a throwaway copy of `openspec/`

## 2. Rules and docs

- [x] 2.1 Update CLAUDE.md (specs section, Git, GitHub issues) and `openspec/config.yaml` (rules, archive guidance); verify by review against the delta spec
- [x] 2.2 Add `.github/pull_request_template.md` and rewrite the flow in `CONTRIBUTING.md`; verify by review
- [x] 2.3 Update the skills `harness-git-workflow` and `harness-write-scenario`; verify by review
- [x] 2.4 Update the wiki page `docs-and-specs.md` and the wiki log; verify with `wiki.py check`
- [x] 2.5 Add the change to `CHANGELOG.md`; verify by review

## 3. Archive

- [x] 3.1 This change has nothing to build: archive it in its single pull request before review; verify that `openspec list` does not show it
