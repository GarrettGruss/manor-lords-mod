## 1. Performance
- [ ] 1.1 Measure the game clock rate with and without a Meshy mesh in view. Verified by two real runs and ranges in `notes/frame-time.md`.

## 2. Look
- [ ] 2.1 Make 2 or 3 material variants and take screenshots with `ctx.screenshot`. Verified by pictures in `evidence/` listed in `evidence/README.md`. The user picks one.
- [ ] 2.2 Check the normal map look. Verified by the same pictures.
- [ ] 2.3 Check collision of a prop part with a unit walking into it. Verified by a real run and a note.

## 3. Tests
- [ ] 3.1 Add fake tests for `genimage.py` and the pure functions of `meshy_material.py` and `recook_meshy_pak.py`. Verified by `uv run python -m unittest discover -s harness/tests -p "test_*.py"`.

## 4. Close
- [ ] 4.1 Update the wiki page for the mesh pipeline, the skill `harness-meshy` and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 4.2 Close issues #102 and #237 with a comment. Verified by the issue state.
- [ ] 4.3 Fill the test results table of the implementation pull request.
