## Why

Issue #408. Depends on change `add-motion-story-skill` (#407).

The Invasion Mod needs a trailer for YouTube, 60 seconds or less. The owner wrote the script in `design/mod/trailer.md` (draft, 2026-10-16). The owner wants it built as a scroll-driven web story with the `sn-motion-html` skill, and then exported as a video from the same story (chat, 2026-10-22). The owner waived the gate 1 pull request for this change (chat, 2026-10-22).

Design served: `design/mod/invasion-mod.md`, vision (a lieutenant lord in Franconia during the Hussite Wars). The trailer shows pillar 4 (dread from knowing: the army on the map), pillar 6 (one path of rule: "Rule by fear, or by faith"), and raids and refugees. It keeps the tone rule of the script: the narrator hates the Hussites for what they do to his people, and the trailer does not draw them as evil. It adds no game behavior, so it cannot break a pillar.

Source material: the legacy animatic spec 27 (`openspec/changes/archive/2026-10-16-legacy-27-trailer-animatic/`).

## What Changes

- New story project `trailer/` made with the skill (`init_project.py`), with the story data, prompts and manifests in git, and generated media out of git.
- Chapters follow the shot list of `design/mod/trailer.md`. Story part (0:00 to 0:28): woodcut and manuscript stills, Seedance scene clips and burning-page connectors. Gameplay part (0:28 to 0:48): real game footage captured with the harness, placed in the same stage. End (0:48 to 1:00): split frame, map, black, title card.
- Style: ink lines, parchment, black, bone white, ember orange, dried-blood red; red seal chapter marks; serif type; all spoken lines in English (the owner dropped the Czech lines, 2026-10-23).
- Each side is known by its banner: a banner reference image in `references/banners.png` (owner request, 2026-10-23).
- The scroll page works on desktop and phone width.
- The video export is 1920x1080, 30 frames per second, 60 s or less, with the voice and music track muxed in when it exists.

## Non-goals

- Recording the voices and making the music. The export uses a finished audio file, or exports silent.
- Changes to the story. The owner owns `design/mod/trailer.md`. The open points listed there stay with the owner.
- Public hosting and the YouTube upload.

## Capabilities

### New Capabilities

- `mod/trailer`: the trailer story page and its video export. It is not a Lua feature folder; it is the mod's promotional media.

## Impact

- New folder `trailer/`.
- `design/mod/trailer.md` is read, not changed.
- Paid generation: Gemini stills (small cost) and Seedance clips (higher cost). Each paid batch needs the owner's cost approval (`process/trailer-production`).
- Gameplay capture needs the game and a test scenario with screenshots or a screen capture.
