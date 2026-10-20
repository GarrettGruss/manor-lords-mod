---
name: harness-meshy-agent
description: Use the Meshy 3D agent CLI (meshy-cli and the meshy-3d-generation skill) for Meshy modes that genmesh.py lacks, then feed the result into the harness-meshy import and pak steps. Use only after the owner has installed it by hand.
---

# Meshy 3D agent pipeline

Review of the source: `install-review.md`. Read it first.

## When to use it
- Default: use `harness-meshy` (`genmesh.py`). It has credit caps, a log and `resume`.
- Use this skill only for a Meshy mode that `genmesh.py` lacks (text-to-3d variants, retexture, remesh, rig), or when the owner asks.
- The import, material and pak steps (3 to 6 of `harness-meshy`) stay the same.

## Setup (the OWNER runs these by hand; an agent must not)
Source: https://raw.githubusercontent.com/meshy-dev/meshy-3d-agent/refs/heads/main/INSTALL.md (MIT repo).
Safety review points before you run anything:
1. Read `skills/*/SKILL.md` and `references/` of the repo, and the `meshy-cli` package page. They run or steer an agent with your rights.
2. Pin the versions: `npm install -g meshy-cli@0.4.3`. Do not use `npx -y` with an unpinned package. Prefer a skill install that does not use `-g -y`, or copy the reviewed skill into `.claude/skills/` and commit it.
3. Never use `sudo`. Needs Node.js 22.12 or newer.
4. Sign in with `meshy auth login --device` (browser code at meshy.ai/device). Use the existing Pro plan account. Never create an account, buy credits or change the plan.
5. Do not add an MCP server and do not change `.claude/settings.json` or `.mcp.json` for it.
6. Check the balance: `meshy balance --format json --no-update-check`.

## Pipeline
1. Reference: Gemini images or a text prompt (`harness-meshy` step 1).
2. Generate with `meshy` (CLI) or the agent skill. Stay within the caps of `harness-meshy`: 60 credits per call, 200 per day. The CLI does not enforce them, so check the balance before and after.
3. Download the model to git-ignored `runs/genmesh/<name>/`. Keep the same file names as `genmesh.py` output so the import scripts work.
4. Record the task id and credits by hand in `openspec/changes/<change-name>/notes/meshy-assets.md` (`genmesh.py` does not log CLI tasks).
5. Import, cook, pak and test: `harness-meshy` steps 3 to 6 (grey material rule applies).

## Keys and secrets
- Never commit or write an API key, a token or the CLI session file in the repo.
- Meshy output is shipped under the Pro plan terms quoted in `harness-meshy`.

## Links
- `harness-meshy`, `harness-pak-mod`
- Wiki: `docs/wiki/workflows/meshy-models.md`
- Source repo: https://github.com/meshy-dev/meshy-3d-agent
