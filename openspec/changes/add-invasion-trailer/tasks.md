## 1. Plan (no paid calls)

- [x] 1.1 Make the project `trailer/` with `init_project.py`. Verified by `serve_project.py` showing the template.
- [x] 1.2 Write the style preamble and identity blocks (Jan Hus, the Bohemian captain, the chalice banner, the narrator). Verified by owner review.
- [x] 1.4 Make the banner reference image `references/banners.png` (Gemini, small cost) and list it in `references/README.md` with its prompt and model. Verified by owner review.
- [x] 1.3 Write the storyboard: chapter, subject, camera move, copy position, connector, time in the video. Verified by owner review (shot plan approval).

## 2. Stills

- [x] 2.1 Make 3 test stills (opening, middle, end) with Gemini. Verified by owner approval of the style.
- [ ] 2.2 Make the full still set after both approvals. Verified by a contact sheet and owner review.

## 3. Clips (each batch needs cost approval)

- [ ] 3.1 Dry run of the manifest; show the clip count, durations and cost. Verified by owner cost approval.
- [ ] 3.2 One representative clip. Verified by owner review.
- [ ] 3.3 All scene clips, then all connectors. Verified by `verify_media.py` and a contact sheet.

## 4. Gameplay part

- [ ] 4.1 Capture the gameplay shots (smoke on the horizon, looted granary, burning barn, villagers, refugees, bandits) with a test scenario in `mod/InvasionMod/scenarios/`. Verified by a real game run.
- [ ] 4.2 Normalize the captures into the stage timeline. Verified by `verify_media.py`.

## 5. Page and export

- [ ] 5.1 Build the page: copy, seal marks, title card. Verified by browser checks: forward, back, chapter jump, 390 px width, reduced motion.
- [ ] 5.2 Write `content/timing.json` to the shot list. Export the video. Verified by `ffprobe` (1920x1080, 30 fps, 55 to 60 s).
- [ ] 5.3 Picture evidence: stills of each chapter on desktop and phone into `evidence/`. Verified by review.

## 6. Close

- [ ] 6.1 Update the "Checked by" lines, the wiki and `CHANGELOG.md`.
- [ ] 6.2 Run `openspec validate add-invasion-trailer --strict`.
- [ ] 6.3 Archive the change as the last commit.
- [ ] 6.4 Test results table for the implementation pull request.
