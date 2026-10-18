# Spec 34: Repo wiki

Status: built, acceptance run done (2026-10-18). Issue: #244. Branch: `feat/34-repo-wiki`.

## Goal
A code wiki for this repo in `docs/wiki/`. Claude Code sessions write it and keep it current with the project skill `repo-wiki`. No other runtime, model provider or API key is needed.

The format is a compact form of OpenWiki v0.7.2 (MIT, `langchain-ai/openwiki`). The review is in `implementation-notes/openwiki-format-review.md`.

## Non-goals
- Run the OpenWiki CLI, its MCP server or its host integration.
- Claims sidecars (`.claims/*.json`) with line hashes, the page manifest, run state and resume.
- Translation, personal mode, connectors, workspaces, the visualizer, CI recurrence.
- A Mermaid parse check (it needs Node).
- Replace the specs. The wiki explains the current system and links to specs for history and decisions.

## Format
- Pages are Markdown files under `docs/wiki/`, in topic folders such as `architecture/`, `concepts/`, `workflows/`, `operations/`, `integrations/`, `testing/`. The entry page is `docs/wiki/quickstart.md`.
- Each page starts with front matter. Keys: `type`, `title`, `description` (one line), `tags` (list), `sources` (list of repo-relative files or folders; a folder ends with `/`). Other keys are allowed and kept.
- Front matter uses a small YAML subset: `key: value`, `key: [a, b]`, and `key:` followed by `  - item` lines. The tool rejects other syntax.
- `index.md` in each folder is generated. Nobody edits it by hand. The root index has `okf_version: "0.2"` front matter, as in OpenWiki.
- Links are relative to the page. Root-absolute links (`/docs/...`) are errors.
- `docs/wiki/.last-update.json` holds the git commit that the wiki was last checked against.

## Plan
1. Tool `harness/tools/wiki.py` with four subcommands:
   - `index`: write every `index.md` from the front matter of the pages.
   - `check`: validate front matter, source paths, links, heading anchors and indexes. Exit 1 with a list of errors.
   - `stale`: list the pages whose sources changed since the last update (committed and uncommitted changes), and changed paths that no page covers.
   - `stamp`: write `.last-update.json` with the current commit.
2. Tests: `harness/tests/test_wiki_tool.py` (temp repos, no game).
3. Skill `.claude/skills/repo-wiki/SKILL.md`: read the wiki, init it, update it. Page jobs may go to Sonnet subagents, one page for each agent.
4. Acceptance run: init the wiki over this repo with the skill. Notes in `implementation-notes/acceptance-run.md`.

## Result
All five acceptance criteria are met (2026-10-18). The init wrote 24 pages. See `implementation-notes/acceptance-run.md` for the run, the review corrections and the findings.

## Open questions
- `stale` lists map pages with broad sources (`source-map.md`) for almost any change. Group or rank the output later?
- Should a hook or a CI job run `wiki.py stale` and warn when the wiki falls behind? Not in this spec.
- Should feature branches update the wiki in the same PR? Proposed: yes, when `stale` lists pages for the changed files.

## Acceptance criteria
1. `uv run python -m unittest harness/tests/test_wiki_tool.py` passes.
2. An init run with the skill writes `docs/wiki/` with `quickstart.md` and pages that cover `mod/`, `harness/`, `mcp/` and the doc tracks.
3. `uv run python harness/tools/wiki.py check` reports no errors on the result.
4. After `stamp`, `stale` lists no stale pages. With `--since` set to an older commit, it lists the pages whose sources changed.
5. The skill and `harness-overview` name the tool and the wiki.
