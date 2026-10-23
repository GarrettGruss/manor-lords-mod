## ADDED Requirements
<!-- Issue: #408 -->

### Requirement: The trailer is one continuous scroll story
The trailer page SHALL show the chapters of `design/mod/trailer.md` in order, on one fixed full-screen stage. Scroll progress SHALL drive one ordered timeline of scene clips and connector clips. Each chapter SHALL show its copy as HTML text over the artwork, without a solid card, and the copy SHALL fade out during connectors.

#### Scenario: Forward and back
- **WHEN** a viewer scrolls from the first chapter to the last, and back to the first
- **THEN** the stage shows each chapter in order both ways, with no blank frame
- Not checked yet.

#### Scenario: Chapter jump
- **WHEN** a viewer selects a chapter mark
- **THEN** the stage shows that chapter and its copy
- Not checked yet.

#### Scenario: Phone width
- **WHEN** the page is shown at 390 px width
- **THEN** each chapter's focal subject and copy are both visible, and the page has no horizontal scroll
- Not checked yet.

### Requirement: The trailer has one visual style
All stills and clips SHALL use one style preamble: woodcut or manuscript ink lines, parchment texture, and the palette black, bone white, ember orange and dried-blood red. Connectors in the story part SHALL use burning page edges or drifting embers. Gameplay footage SHALL keep its own look, framed by the same page treatment.

#### Scenario: Style review
- **WHEN** the owner reviews the contact sheet of all clips
- **THEN** the owner approves the style of each story clip
- Checked by review.

### Requirement: The trailer exports as a video of 60 seconds or less
The export SHALL make an MP4 at 1920x1080, 30 frames per second, H.264, of 60 s or less, from the same story data as the page. The scene times SHALL follow the shot list times within 0.5 s. When an audio file is given, the video SHALL hold it as its only audio track.

#### Scenario: Export check
- **WHEN** the trailer is exported
- **THEN** `ffprobe` reports 1920x1080, 30 frames per second and a duration between 55 and 60 s
- Not checked yet.

#### Scenario: All spoken lines are in English
- **WHEN** the Bohemian voice or the narrator speaks
- **THEN** the line is in English and the frame shows no subtitle; only the Latin line of Hus and the Hussite hymn over the title are not in English
- Checked by review.

### Requirement: The trailer keeps the tone of the script
The narrator SHALL hate the Hussites for what they do to his people. The copy and images SHALL NOT draw the Hussites as monsters or as evil; they SHALL show what the Hussites do. Historical claims in the copy SHALL match the facts listed in `design/mod/trailer.md`.

#### Scenario: Copy review
- **WHEN** the owner reviews the shot plan and the copy
- **THEN** the owner approves the tone and the facts
- Checked by review.

### Requirement: Each side is known by its banner
Every still, panel and clip that shows an army SHALL show the banner of its side, as drawn in the banner reference image `references/banners.png` of this change. Banners SHALL carry no readable text. The details are in `design/trailer/invasion-mod/slow/02-mood-board.md`, section Banners.

#### Scenario: Hussite banner
- **WHEN** a frame shows the Hussites
- **THEN** their banner is a gold chalice (a cup with a foot and a stem, no gems) on a red field, on a tall, narrow banner, as in the Jena Codex
- Checked by review.

#### Scenario: Crusader banner and the king's seal
- **WHEN** a frame shows the crusaders or the king's seal
- **THEN** the crusader banner is a red cross on a white field, and the seal is a black eagle on gold
- Checked by review.

#### Scenario: Militia banner
- **WHEN** a frame shows the narrator's militia
- **THEN** it carries the player's heraldry from the game, and that heraldry does not use the Hussite red and gold
- Checked by review.

#### Scenario: The reference image exists
- **WHEN** the change is validated
- **THEN** `references/banners.png` exists in the change folder and is listed in `references/README.md` with its prompt and model
- Not checked yet.
