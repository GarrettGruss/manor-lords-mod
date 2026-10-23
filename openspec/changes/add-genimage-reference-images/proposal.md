## Why

Issue #414.

`harness/tools/genimage.py` sends only a text prompt. Stills for a story or a trailer must keep one look across many images, and text alone drifts. Gemini image models accept images in the same request. With a reference image, a new still can follow a style anchor (for example a public domain manuscript page) or an earlier approved still.

First use: the trailer storyboard (change `add-invasion-trailer`, #408). The review of the historical reference images (owner request, 2026-10-23) picked three public domain style anchors and found that the tool cannot take them.

## What Changes

- New option `--ref <file>` for `genimage.py`, given 1 to 3 times. Each file is sent as an image part before the text prompt, in the same request.
- Only Gemini models take references. With an Imagen model, `--ref` stops the tool with a clear message and no API call.
- Each reference must exist, be PNG, JPEG or WebP, and be at most 7 MB. A bad file stops the tool before any API call.
- The log line of each call also lists the reference files and their SHA-256 hashes, so a still can be traced to its anchors.
- New unit tests with a fake API call. No paid call in the tests.

## Non-goals

- Image editing or masks.
- Downloading references from a URL. References are local files.
- Checking the license of a reference. The person who picks a reference checks it (see Impact).

## Capabilities

### Modified Capabilities

- `harness/mesh-pipeline`: the requirement "Reference images from Gemini" gains reference image input.

## Impact

- `harness/tools/genimage.py`, a new test file `harness/tests/test_genimage.py`.
- The skill `harness-meshy` names `genimage.py`. Its usage line is updated in the same commit.
- Cost: a reference image adds input tokens to a call. The cost per image stays small; the log shows each call.
- Licensing: a reference must be one the user may use, for example public domain by age, or the user's own work. The tool does not check this.
