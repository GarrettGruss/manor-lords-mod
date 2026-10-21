## 1. Decisions
- [ ] 1.1 Ask the user the four questions in `design.md`. Verified by the answers in `design.md`.

## 2. Version 0
- [ ] 2.1 Add the packages with `uv add` and check for ffmpeg at start. Verified by `uv run python trailer/build.py --help` and a test of the missing tool message.
- [ ] 2.2 Write the shot list reader and the length and source checks. Verified by `harness/tests/test_trailer_build.py` (no ffmpeg).
- [ ] 2.3 Write `build.py` for text cards with a TTS voice. Verified by a local build of a 60 second draft.
- [ ] 2.4 Write the timing and audio reports on data. Verified by `harness/tests/test_trailer_timing.py` with a planted overrun and a planted silence.
- [ ] 2.5 Write `review.py` (sheets, key frames, transcript, summary). Verified by a run on the draft and a token count of the pack (8000 or less).
- [ ] 2.6 Check that picture evidence is stored: put 2 contact sheets of the draft in `evidence/` (visual result). Verified by `evidence/README.md`.

## 3. Close
- [ ] 3.1 Write the wiki page for the pipeline, a skill note, and `CHANGELOG.md`. Verified by `wiki.py check`.
- [ ] 3.2 Close issue #133 with a comment after the merge. Verified by the issue state.
- [ ] 3.3 Fill the test results table of the implementation pull request.
