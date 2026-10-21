## Purpose
<!-- Issue: #133 -->
The trailer pipeline builds a draft trailer video from a timed shot list and turns a video into a small review pack that an agent can read. The agent cannot play video or audio, so the pack holds contact sheets, a timed transcript and timing and audio reports.

## ADDED Requirements

### Requirement: A shot list builds a draft video
The tool `trailer/build.py` SHALL read the shot list `trailer/trailer.yaml` and write `trailer/out/v<N>.mp4`. Each shot SHALL have a start, an end and a type (`panel`, `gameplay`, `black` or `title`). A shot with a missing source SHALL become a text card with its description.

#### Scenario: A text card draft
- **WHEN** the shot list has only text card shots with a voice line each
- **THEN** the tool writes an mp4 with the voice and the subtitles
- **AND** the total length is 60 seconds or less
- Not checked yet (planned: `harness/tests/test_trailer_build.py`).

### Requirement: The build fails loudly
The build SHALL fail with a clear message when the total length is over 60 seconds, when a source file is missing for a shot that is not a text card, or when ffmpeg is not installed.

#### Scenario: A trailer that is too long
- **WHEN** the shot list ends at 61 seconds
- **THEN** the build exits with an error that names the total and the limit
- Not checked yet (planned: `harness/tests/test_trailer_build.py`).

#### Scenario: A missing tool
- **WHEN** ffmpeg is not on the path
- **THEN** the build exits with an error that names ffmpeg
- Not checked yet (planned: `harness/tests/test_trailer_build.py`).

### Requirement: A review pack is small
The tool `trailer/review.py <video>` SHALL write `trailer/out/v<N>-review/` with contact sheets (16 frames each, one frame per second by default, each with a time stamp), key frames for shots marked `key: true`, a transcript with time stamps, `timing.md`, `audio.md` and `summary.md`. The pack of a 60 second video SHALL cost the agent 8000 tokens or less to read.

#### Scenario: The pack of a 60 second video
- **WHEN** the review tool runs on a 60 second video
- **THEN** the folder holds 4 contact sheets, the transcript, the two reports and the summary
- **AND** the summary lists the problems and the files to open
- Not checked yet (planned: `harness/tests/test_trailer_review.py`).

### Requirement: Timing problems are found
The timing report SHALL name each voice line that runs past its slot, each shot shorter than 1 second, and each subtitle shown too briefly to read. The audio report SHALL list silences and loudness. These checks SHALL run without ffmpeg in unit tests, on data.

#### Scenario: A voice line that runs over
- **WHEN** a voice line is 6 seconds long and its slot is 4 seconds
- **THEN** `timing.md` names the line and the 2 second overrun
- Not checked yet (planned: `harness/tests/test_trailer_timing.py`).

#### Scenario: A silence in the audio
- **WHEN** the version 0 build has no sound from 0:54 to 0:57
- **THEN** `audio.md` lists that silence
- Not checked yet (planned: `harness/tests/test_trailer_timing.py`).
