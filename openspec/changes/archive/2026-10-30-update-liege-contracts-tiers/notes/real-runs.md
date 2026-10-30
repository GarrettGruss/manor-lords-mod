# Real game runs (slot 1, private pak config)

| Test scenario | Start | Run id | Verdict |
|---|---|---|---|
| `liege-contracts-window` | default fixture (manor) | 20261030-182600-a361 | pass |
| same | default fixture (manor) | 20261030-182726-274d | pass |
| same | `--new-game` (no manor) | 20261030-182844-9c14 | pass |
| same | `--new-game` (no manor) | 20261030-183004-323f | pass |
| `liege-contracts-fulfil` | default fixture | 20261030-183650-7d2b | pass |
| same | default fixture | 20261030-184053-c309 | pass |
| `liege-contracts-roundtrip` write phase | default fixture | 20261030-183843-2702 | pass (slot saveGame_56, guarded `save_game`) |
| same, read phase | `--save saveGame_56.sav` | 20261030-183937-1af3 | pass |

Failed or fixed runs on the way (all harness or mod findings, no game crash): 20261030-181412-9ac0 and the next three (stale pak from the shared work folder, see `window-controls.md`); 20261030-182223-1fa0 (no mouse); 20261030-183206-25f3 and 20261030-183324-6191 (see findings); 20261030-183513-6d47.

## Findings

- No mouse device: this PC reports `SM_MOUSEPRESENT = 0`, so real mouse scenarios (also `menu-smoke`, `invasion-raid-widget` on this PC) stop with an InputError. The window scenario uses the new command `liege_menu_press` (the same code as a click). A real mouse click on a Fulfil button is NOT verified.
- Food lies in a building of type 80 (berries: "the goods lie type 80: 70"), not in the stores of types 6 and 72. The first take found 0 of 70. `world.take_goods` now takes from every building of the region that holds the good (known stores first, never a home). Armour and goods in other buildings follow the same rule.
- The stock number can count one unit that is in no store: helmets 8 found of 9 (run 20261030-183513-6d47). The take is refused with the message and the units taken are put back.
- Regional wealth: see `regional-wealth.md`. Season days: see `season-days.md`.
- Not run in the real game: `liege-influence-roundtrip` (updated, needs a second kept save), a second roundtrip pair (each pair leaves a kept save in the user's save folder; `saveGame_56` stays there, a deletion was not allowed).
