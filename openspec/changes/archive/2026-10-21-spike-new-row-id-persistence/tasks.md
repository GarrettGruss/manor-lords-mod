## 1. Real game checks
- [x] 1.1 Place and build a new id building, make a harness save with `save_game`, load it, read the building. Verified by a real run and the save guard (user saves unchanged).
- [x] 1.2 Use a new upgrade row (research, then read the effect). Verified by a real run and a note. Result: negative, new upgrade ids are not carried out (notes/id-persistence.md).
- [x] 1.3 Run an AI lord village with the new ids in the pak for 30 game days. Verified by a real run: no crash, no error lines in the lord debug logs.

## 2. Result
- [x] 2.1 If a range fails, change the id rule and ask the user. Verified by a changed requirement in `harness/pak-mods` and `openspec validate`. Owner decision 2026-10-21: accept the limit.
- [x] 2.2 Write `notes/id-persistence.md`. Verified by review.
- [x] 2.3 Update `CHANGELOG.md` if the rule changes. Verified by review.
- [x] 2.4 Fill the test results table of the implementation pull request.
