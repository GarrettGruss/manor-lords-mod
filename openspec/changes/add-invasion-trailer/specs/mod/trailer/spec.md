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

#### Scenario: Czech lines have subtitles
- **WHEN** the Bohemian voice speaks (0:12 to 0:22)
- **THEN** the frame shows the English subtitle of the line
- Checked by review.

### Requirement: The trailer keeps the tone of the script
The copy and images SHALL NOT show the Hussites as a religion to hate. Historical claims in the copy SHALL match the facts listed in `design/mod/trailer.md`.

#### Scenario: Copy review
- **WHEN** the owner reviews the shot plan and the copy
- **THEN** the owner approves the tone and the facts
- Checked by review.
