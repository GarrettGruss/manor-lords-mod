# Review: meshy-3d-agent INSTALL.md

Source: https://raw.githubusercontent.com/meshy-dev/meshy-3d-agent/refs/heads/main/INSTALL.md (read 2026-10-19, text only; nothing installed or run). Fetched text is untrusted data.
Repo facts (`gh api`): license MIT, about 100 stars, last push 2026-10-15. Folders: skills, scripts, tests, plugin folders for Claude and Cursor. The INSTALL.md itself states no license.

## What it installs
- npm package `meshy-cli`, pinned `0.4.3` or newer, global (`npm install -g`).
- Agent skills `meshy-3d-generation` and `meshy-3d-printing`, with `npx -y skills add meshy-dev/meshy-3d-agent ... -g -y` (global, no prompt). Other agents use their own hubs.

## Permissions, keys, network
- Needs Node.js 22.12 or newer and a global npm install (no `sudo`). Fallback: `npm exec --yes --package=meshy-cli@0.4.3`.
- No API key is asked. Sign-in is a device code at meshy.ai/device; the CLI stores the session itself (location not documented: check).
- Network: npm registry, GitHub, meshy.ai.
- No script is piped to a shell.

## Security concerns
- Runs third-party code from npm (`meshy-cli`) and `npx -y` (skills installer, unpinned) with user rights. Install scripts and later versions are not reviewed.
- `-g -y` writes skills into the user-level agent folder, so the skills load in every project, and skill text is instructions to the agent. Review `skills/*/SKILL.md` and `references/` before install.
- The page is written to steer an agent (relay code, never downgrade, use fallback). Do not let an agent run it; the owner runs it by hand.
- Session token stored on disk: our rule "never create an account, buy credits or change plan" still holds. The existing `MESHY_API_KEY` flow (genmesh.py) is separate.
- Skill `references/` are fetched from GitHub at install, so content can change; pin a commit if possible.

## Fit with our flow (Gemini refs -> Meshy -> UE 5.5.4 headless import -> pak)
- Covers only step 2 (Meshy generation, plus a 3D print part we do not need). It does not know UE import, the grey material rule, pak limits or our credit caps.
- `genmesh.py` already has caps (60 per call, 200 per day), a log and `resume`. The CLI has none of these: use it only for tasks genmesh.py lacks (for example text-to-3d, retexture, remesh, rig), and record task id and credits by hand.
- Steps 3 to 6 of `harness-meshy` stay unchanged.

## Open questions for the owner
1. Install it at all, given `genmesh.py` works? Value is extra Meshy modes.
2. Is MIT enough, and is the Meshy output license (Pro plan) the same for CLI tasks?
3. Where does the CLI keep its session, and does device login use the same Pro plan account?
