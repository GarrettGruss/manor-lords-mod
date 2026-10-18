# Changelog

All notable changes to PolicyMenu are in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The version follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- A click is a hook event of a click button (shared module `HarnessClickHooks`), not a poll of `Button:IsPressed`. A short click is no longer missed. The tick is 100 ms (was 40 ms). The pak holds `Border` slots and `WBP_ClickButton`. New command `PolicyMenu.press`. The mod needs the shared modules `ManorCore` and `HarnessClickHooks`.

## [0.1.0] - 2026-10-14

First pre-release for play testers.

### Added
- A policy menu. It lists every policy that your village can sign now, with the name from the game.
- A click on a policy signs it. A click on a signed policy unsigns it. A signed policy shows a mark ([x]) and a green button.
- F7 opens and closes the menu.
- The menu is a Widget Blueprint in the pak policymenu_P.pak. The mod needs only the shared module ManorCore.
