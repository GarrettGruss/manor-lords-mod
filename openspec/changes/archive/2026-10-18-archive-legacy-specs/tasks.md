# Tasks

## 1. Coverage data first

- [x] 1.1 Do the change `move-coverage-criteria-to-openspec` (#279) on this branch, so no tool reads a legacy folder; verify with `coverage.py --check-spec` and `test_coverage.py`

## 2. Move and rewrite

- [x] 2.1 Record the broken relative links before the move; verify with the link checker (9, all example links in the OKF reference)
- [x] 2.2 Move the 49 legacy entries with `git mv` and rewrite all references with a script that keeps line endings; verify with the link checker (still 9) and `git diff --numstat` (no whole-file rewrites)
- [x] 2.3 Remove `docs/harness/README.md`, rewrite `design/mod/README.md`; verify that no reference outside the `CHANGELOG.md` files names an old path

## 3. Rules and docs

- [x] 3.1 Write the MODIFIED delta of `process/spec-workflow`; update CONTRIBUTING.md, `openspec/config.yaml`, the skills and the wiki; verify with `openspec validate --all --strict` and `wiki.py check`
- [x] 3.2 Add the change to `CHANGELOG.md`; verify by review

## 4. Checks and archive

- [x] 4.1 Run `lua_syntax.py`, a compile of the changed Python files, and the full Python tests on `main` and on the branch; verify that the results are the same
- [x] 4.2 Archive this change before the pull request; verify with `openspec list`
