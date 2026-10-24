## 1. Build
- [ ] 1.1 Unpack the widget assets from the old paks into `data/<feature>/assets/`.
- [ ] 1.2 Build `InvasionMod_P.pak` with `pakmod.py buildmod InvasionMod` and check its file list.
- [ ] 1.3 Set `mod.json` pak to `InvasionMod`; remove `raidmenu_P.pak` and `techmenu_P.pak`.

## 2. Callers
- [ ] 2.1 Replace `--pak raidmenu` and `--pak techmenu` in scenarios, Lua messages and comments.
- [ ] 2.2 Update the skills and the wiki.
- [ ] 2.3 Add a test that the manifest pak is `InvasionMod` and that the committed pak holds each widget.

## 3. Proof
- [ ] 3.1 Real runs: new game with the 6th template and the mod menu; raid widget; tech tree widget; liege screen with the arms button.
- [ ] 3.2 Release dry run: the zip holds only `InvasionMod_P.pak`.
- [ ] 3.3 Full test set, CHANGELOG, `openspec validate --strict`, archive.
