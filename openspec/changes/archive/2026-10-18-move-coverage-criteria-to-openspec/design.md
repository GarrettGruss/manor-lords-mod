# Design: Move coverage criteria to openspec

## Open questions
| Question | Who decides | Notes |
|---|---|---|
| Where do the files live? Proposal: `openspec/specs/harness/coverage/criteria.json` and `criteria.md` | The user | `openspec validate` ignores extra files in a spec folder. Check that `openspec archive` keeps them. |
| Do the criteria tables stay in a Markdown document that `--check-spec` parses, or does the JSON become the only source? | The user | Today two copies are checked against each other. One source is simpler. |
| Does the legacy copy get a note that it is frozen? | The user | The legacy folders are read only, so a note is a change of a legacy file. |

## Decision D1: copy first, then switch
Copy the data, switch the defaults, run `--check-spec`, and only then update the docs. This keeps the tool working at each commit.

## Decisions taken (2026-10-18)

The user accepted the plan to move the coverage data together with the legacy specs ("I accept", 2026-10-18). The proposals of the open questions were taken:
- D2: the files are `openspec/specs/harness/coverage/criteria.json` and `criteria.md`. A test archive on a copy of `openspec/` keeps both files.
- D3: the tables stay a Markdown document that `--check-spec` compares with the JSON. The tool behavior does not change; only its default paths change.
- D4: the legacy copy gets no note. The whole legacy folder moves into the archive in the change `archive-legacy-specs`.
