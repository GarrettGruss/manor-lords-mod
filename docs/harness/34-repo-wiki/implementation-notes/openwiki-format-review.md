# OpenWiki format review

Source: a clone of `langchain-ai/openwiki` v0.7.2 (commit `6c14bff`) in `../openwiki`. Read only. No code from it ran. Date: 2026-10-18.

## Why not the CLI
- `openwiki code --init -p` failed: `OPENAI_API_KEY is required for non-interactive runs`. The installed CLI uses OpenAI as the model provider.
- The host mode (`openwiki integrations install claude --project`, `src/integrations/install/registry.ts:46`) lets Claude Code drive OpenWiki through an MCP server. It needs no API key. But it needs the Node `openwiki` runtime on each machine, it writes into `.mcp.json` (which here holds Windows paths), and it keeps the full format below.

## Two layers in OpenWiki
1. Model instructions, about 600 lines:
   - `src/agent/repository-prompts.ts`: planner prompt (explore, then plan a page tree around systems and workflows, not the source tree) and page prompt (one worker owns one page; research, then write; on update keep accurate content).
   - `src/agent/prompts/code.ts`: front matter rules (OKF v0.2), link and index rules, security rules (no secrets, no `.env`).
   - `src/claims/guidance.ts`: what a claim is (one material, falsifiable system truth with `repo://path#Lx-Ly` evidence).
   - `integrations/openwiki/SKILL.md`: the same method, written for a host agent.
2. Deterministic code after the model, several thousand lines:
   - Front matter repair and the `generated` provenance stamp (`src/okf/frontmatter.ts`, `generated-provenance.ts`).
   - `index.md` for each folder from page titles and descriptions (`src/okf/index-sync.ts`).
   - Link and anchor check; broken links get an HTML comment (`src/agent/wiki-link-validator.ts`).
   - Mermaid parse check; a bad diagram becomes a text block (`src/mermaid/`).
   - Claims sidecars `.claims/<page>.json` with opaque line hashes, used to find stale facts and relocate moved lines (`src/claims/`).
   - Page manifest `.page-manifest.json` with the git head of each page, used to scope updates (`src/generation/page-manifest.ts`).
   - Run state, the page queue and the MCP lifecycle (`src/generation/repository-run.ts`, `src/integrations/`).

## What spec 34 keeps
| OpenWiki | Spec 34 |
|---|---|
| Page tree with `quickstart.md` | Same, under `docs/wiki/` |
| OKF front matter `type`, `title`, `description`, `tags` | Same, plus `sources` |
| Generated `index.md` | `wiki.py index`, same layout |
| Link and anchor check | `wiki.py check` (fails, does not mark) |
| Claims with line hashes | `sources:` list of files and folders; staleness by changed file |
| Page manifest and `.last-update.json` | One `.last-update.json` with the git commit |
| Run state and resume | Not needed: a Claude session and a git branch |
| Planner and page prompts | Shortened into the skill |

## What is lost
- Facts are not checked line by line. A change to a source file marks all its pages for review, also when the change does not touch the fact.
- No Mermaid parse check.
- The output is not the full OpenWiki format (no `.claims`, no manifest). OpenWiki search tools may still read the Markdown. Not tested.
