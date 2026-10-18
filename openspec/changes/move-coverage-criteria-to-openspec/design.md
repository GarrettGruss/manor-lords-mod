# Design: Move coverage criteria to openspec

## Open questions
| Question | Who decides | Notes |
|---|---|---|
| Where do the files live? Proposal: `openspec/specs/harness/coverage/criteria.json` and `criteria.md` | The user | `openspec validate` ignores extra files in a spec folder. Check that `openspec archive` keeps them. |
| Do the criteria tables stay in a Markdown document that `--check-spec` parses, or does the JSON become the only source? | The user | Today two copies are checked against each other. One source is simpler. |
| Does the legacy copy get a note that it is frozen? | The user | The legacy folders are read only, so a note is a change of a legacy file. |

## Decision D1: copy first, then switch
Copy the data, switch the defaults, run `--check-spec`, and only then update the docs. This keeps the tool working at each commit.
