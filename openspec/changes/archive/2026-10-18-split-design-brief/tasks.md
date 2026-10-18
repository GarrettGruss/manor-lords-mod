# Tasks

## 1. Split and move

- [x] 1.1 Build `design/invasion-mod.md` and `design/decisions.md` from the M00 README, word for word; verify the section lists against the original
- [x] 1.2 Move the M00 README and the feasibility reviews to the archive, and `trailer.md` to `design/`; write `design/README.md`; verify that `docs/mod/` is empty and removed
- [x] 1.3 Rewrite the references (only paths under `docs/mod/M00-invasion-mod` and `docs/mod/README.md`; history text that names the old layout stays); verify that the broken-link count is the baseline (9) and that no old layout path was turned into a `design/` path

## 2. Rules

- [x] 2.1 Write the MODIFIED delta of `process/spec-workflow`; add the vision, the pillars and the proposal rule to `openspec/config.yaml`; verify that the config parses and the pillars reach `openspec instructions proposal`
- [x] 2.2 Add the unanswered M00 open questions to `decide-open-mod-rules`; verify with `openspec validate --strict`

## 3. Docs and archive

- [x] 3.1 Update the wiki source map and log, and `CHANGELOG.md`; verify with `wiki.py check`
- [x] 3.2 Archive this change before the pull request; verify with `openspec list`
