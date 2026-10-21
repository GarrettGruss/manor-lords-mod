# Evidence

Test scenario `liege-tribute-menu`, run `20261020-040052-b793` (`--new-game --pak raidmenu`, verdict pass). Test scenario `liege-send-tribute`, run `20261020-040350-ca20` (`--pak raidmenu`, verdict pass).

| Picture | What it shows |
|---|---|
| `liege-menu-open.jpg` | The tribute menu is open: influence 0, "Tribute: 200 silver (you have 1000)". |
| `liege-menu-after-tribute.jpg` | After a real mouse click on "Send tribute": influence 20, "you have 800". |

In the first pictures the HUD silver of the lord panel showed 0, because a direct write to `playerRef.silver` does not refresh the panel. See `notes/silver-field.md`.
