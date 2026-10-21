## 1. Dependency
- [ ] 1.1 Check that `add-mod-menu-access-rule` (#308) is merged and `core/menu.lua` exists; if not, stop and set the issue `status: blocked`.

## 2. Code
- [ ] 2.1 Add the Pay, Fight and Start raid buttons as content of the raid menu on `core/menu.lua`; verify with fake game tests in `harness/tests/test_fakegame_raid_widget.py`.
- [ ] 2.2 Add the buy-back button with price and disabled state; verify with fake game tests in `harness/tests/test_fakegame_bandits.py`.

## 3. Test scenarios
- [ ] 3.1 Add real game test scenarios that click each button and take pictures; verify with real game runs. Update the "Checked by" lines.

## 4. Close
- [ ] 4.1 Add the pictures and `evidence/README.md`; update the wiki, `CHANGELOG.md`; verify with `wiki.py check`.
