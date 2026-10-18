# Spec: repo-wiki skill

Status: built, acceptance run done (2026-10-18). Issue: #244. Branch: `feat/repo-wiki-skill`.

This spec belongs to the skill, not to the game harness. The skill (`SKILL.md`), this spec, the script `scripts/wiki.py` and the tests `tests/` live together in `.claude/skills/repo-wiki/`. No harness code or harness doc depends on them.

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
- `docs/wiki/` is an Open Knowledge Format (OKF) v0.2 bundle. The spec is copied in `.claude/skills/repo-wiki/references/okf-spec-v0.2.md`. Review: `implementation-notes/okf-conformance.md`.
- Each page starts with YAML front matter (parsed with PyYAML, a dev dependency). This wiki requires `type`, `title`, `description` (one sentence), `tags`, `generated: { by, at }` and `sources` (a list of `{ resource: repo://<path> }` mappings; a folder ends with `/`; `https://` URLs are allowed). OKF optional fields (`verified`, `status`, `stale_after`) are checked when present. Other keys are allowed.
- `index.md` in each folder is generated (OKF section 8). Nobody edits it by hand. The root index has `okf_version: "0.2"` front matter.
- `log.md` (OKF section 9) records each init and update, newest first.
- Links are relative to the page. Root-absolute links (`/docs/...`) are errors, because GitHub resolves `/` from the repo root.
- `docs/wiki/.last-update.json` holds the git commit that the wiki was last checked against.

## Plan
1. Script `.claude/skills/repo-wiki/scripts/wiki.py` with four subcommands:
   - `index`: write every `index.md` from the front matter of the pages.
   - `check`: validate front matter, source paths, links, heading anchors and indexes. Exit 1 with a list of errors.
   - `stale`: list the pages whose sources changed since the last update (committed and uncommitted changes), and changed paths that no page covers.
   - `stamp`: write `.last-update.json` with the current commit.
2. Tests: `.claude/skills/repo-wiki/tests/test_wiki.py` (temp repos, no game).
3. Skill `.claude/skills/repo-wiki/SKILL.md`: read the wiki, init it, update it. Page jobs may go to Sonnet subagents, one page for each agent.
4. Acceptance run: init the wiki over this repo with the skill. Notes in `implementation-notes/acceptance-run.md`.

## Result
All five acceptance criteria are met (2026-10-18). The init wrote 24 pages. See `implementation-notes/acceptance-run.md` for the run, the review corrections and the findings.

## Open questions
- `stale` lists map pages with broad sources (`source-map.md`) for almost any change. Group or rank the output later?
- Should a hook or a CI job run `wiki.py stale` and warn when the wiki falls behind? Not in this spec.
- Should feature branches update the wiki in the same PR? Proposed: yes, when `stale` lists pages for the changed files.

## Acceptance criteria
1. `uv run python -m unittest discover -s .claude/skills/repo-wiki/tests -p "test_*.py"` passes.
2. An init run with the skill writes `docs/wiki/` with `quickstart.md` and pages that cover `mod/`, `harness/`, `mcp/` and the doc tracks.
3. `uv run python .claude/skills/repo-wiki/scripts/wiki.py check` reports no errors on the result.
4. After `stamp`, `stale` lists no stale pages. With `--since` set to an older commit, it lists the pages whose sources changed.
5. The skill names the tool and the wiki, and CLAUDE.md points to the skill. The harness (`harness/`, `docs/harness/`, the harness skills) does not name the skill.
