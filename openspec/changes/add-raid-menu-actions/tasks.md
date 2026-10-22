## 1. Dependency
- [ ] 1.1 Check that `add-mod-menu-access-rule` (#308) is merged and `core/menu.lua` exists; if not, stop and set the issue `status: blocked`.

## 2. Code
- [ ] 2.1 Add the buy-back button with price and disabled state on `core/menu.lua`; verify with fake game tests in `harness/tests/test_fakegame_bandits.py`.

## 3. Test scenarios
- [ ] 3.1 Add a real game test scenario that clicks the button and takes pictures; verify with a real game run. Update the "Checked by" lines.

## 4. Close
- [ ] 4.1 Add the pictures and `evidence/README.md`; update the wiki, `CHANGELOG.md`; verify with `wiki.py check`.
