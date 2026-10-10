# Changelog

All notable changes to this project are listed here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `HarnessLog` shared Lua module. It writes a log file that flushes on each line.
- `HarnessLogTest` mod to check that the log works.
- `harness/deploy.ps1` to copy mods into the UE4SS `Mods` folder and enable them.
- Spec `docs/specs/01-ue4ss-bridge/` with a review checklist.
- Spec `docs/specs/02-save-autoload/` for the save auto-load and ready signal.
- Jmap findings for the game reflection data, in `docs/specs/02-save-autoload/implementation-notes/`.
- `CLAUDE.md` with project rules.
