## 1. Tool

- [x] 1.1 Add `--ref` (0 to 3 files) to `harness/tools/genimage.py`: check each file (exists, PNG, JPEG or WebP by its first bytes, at most 7 MB) before any API call, and send each as an `inlineData` part before the text part. Verified by `harness/tests/test_genimage.py`.
- [x] 1.2 Stop with a clear message when `--ref` is used with an Imagen model. Verified by `harness/tests/test_genimage.py`.
- [x] 1.3 Add the reference files and their SHA-256 hashes to the log line. Verified by `harness/tests/test_genimage.py`.

## 2. Tests

- [x] 2.1 Write `harness/tests/test_genimage.py` with a fake `call_api`: request shape, order of parts, too many references, bad files, Imagen refusal, count range, log line. No network, no key. Verified by `uv run python -m unittest harness.tests.test_genimage`.

## 3. One real call

- [ ] 3.1 Make one still with one public domain reference image, after the owner's cost approval. Verified by the log line and the owner's review of the still.

## 4. Docs and close

- [ ] 4.1 Update the usage line in the docstring and in the skill `harness-pak-mod`, the wiki page `docs/wiki/workflows/meshy-models.md`, and `CHANGELOG.md`.
- [ ] 4.2 Run the full test set and `openspec validate add-genimage-reference-images --strict`.
- [ ] 4.3 Archive the change as the last commit.
