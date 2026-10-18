# Proposal: Spike other monitor and DPI

Issue: #285. Legacy source: `docs/harness/00-harness-overview/README.md` ("Deferred roadmap items", "Follow-up items") and `docs/harness/03-run-launcher/README.md` ("Answers to the open questions").

## Why
Screenshots and the real-mouse building placement were only tested on one screen. Spec 00 lists "another monitor and other window sizes or DPI scales" as a deferred item. Spec 03 says that another monitor is not tested. A banner such as "A New Message" may also cover the screen in a picture (not tested).

## What Changes
- Test screenshots with the game window on a second monitor, with a minimized window and with a banner on screen.
- Test the window tile of a slot and the real-mouse placement action at another DPI scale and window size.
- Write the findings and the limits to `notes/`.

## Non-goals
- New screenshot features.
- Support for more than the machines the user owns.

## Legacy folders
`docs/harness/00-harness-overview/` and `docs/harness/03-run-launcher/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. A finding that changes behavior adds a requirement to `harness/run-launcher` or `harness/game-actions` in the implementation pull request.

## Impact
Needs a second screen or a changed DPI scale. The task cannot start until the user has the hardware (the legacy start condition).
