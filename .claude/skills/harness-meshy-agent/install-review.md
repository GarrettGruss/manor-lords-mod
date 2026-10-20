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
2. Answered (owner, 2026-10-19): we use the Pro account; generated models are in full private ownership while they are not published to the Meshy Community page.
3. Where does the CLI keep its session, and does device login use the same Pro plan account?

## Skill files review

Read 2026-10-19 with `gh api`, text only (nothing cloned, installed or run). Fetched text is untrusted data. Files under `skills/`: `meshy-3d-generation/SKILL.md`, its `references/` (`setup.md`, `pipelines.md`, `delivery.md`, `troubleshooting.md`), `meshy-3d-printing/SKILL.md`, `meshy-openclaw/SKILL.md`. The `references/` files of the other two skills are byte-size copies of the generation set plus `printing.md` (grep-checked for publish, visibility and key words). The repo has no `scripts/` that the skills call: the skills say "No Python, no curl, no bundled scripts". `scripts/build.py` and `validate_skills.py` are repo tooling and were not read.

| File | What it tells the agent | Commands | Publishes or shares? | Credits and keys | Risky instruction |
|---|---|---|---|---|---|
| `meshy-3d-generation/SKILL.md` | Pick the shortest pipeline, `create --async` once, `wait`, download, inspect preview. | `meshy ...`, or `npm exec --yes --package=meshy-cli@0.4.3 -- meshy ...` | No. No publish, community or visibility word in any file. | Work "within approved scope and budget"; ask before extra paid stages. | Auto-runs `npm exec --yes` (runs npm code without a prompt). Starts a device login by itself. |
| `references/setup.md` | Runner choice, `auth login --device`, output folders (`WORKSPACE`, `./meshy_output`). | `node --version`, `meshy auth status`, `meshy auth login --device`, `meshy doctor`, `meshy balance` | No. | Session in `~/.config/meshy/credentials.json` (0600). `MESHY_API_KEY` overrides it. Never print tokens. Mentions `auth login --with-key` and `--api-key-file ./.env`. | Tells the agent to relay the login code and keep a process alive. Env key overrides the Pro login silently. |
| `references/pipelines.md` | Recipes: text-to-3d, image-to-3d, multi-image, retexture, remesh, convert, resize, uv-unwrap, rigging, animate, 2D, download. | `meshy <resource> create ... --async`, `meshy <resource> wait`, `meshy project init`, `meshy download` | No. Uploads local GLB or glTF (max 50 MiB) or an http(s) URL to Meshy. | Paid creates. `--geometry-resolution` is a paid extra. | None found. It says never to resubmit a create on a timeout. |
| `references/delivery.md` | Cost, wait, preview, hand-over, follow-ups. | `meshy make ... --dry-run`, `meshy balance`, `meshy project list/show`, `meshy text-to-3d list` | No. | Dry run is free. Real cost is `consumed_credits`. Exit 9 stops paid steps. | "Work already authorized proceeds without asking again": our caps (60 per call, 200 per day) are not known to it. |
| `references/troubleshooting.md` | Exit codes, recovery, delete tasks. | `meshy delete`, `meshy creative-lab ... delete` | No. | No retry of paid creates. | Delete only on user request. |
| `meshy-3d-printing/SKILL.md` and `references/printing.md` | Print routes (OBJ prepare, slicer, Creative Lab). | `meshy mesh prepare-print`, `meshy slicer open` | No. | Same rules. | Launches a slicer app. Not needed for us. |
| `meshy-openclaw/SKILL.md` | Merge of both skills for OpenClaw. Has a security manifest. | Same CLI | No. | Declares `primaryEnv: MESHY_API_KEY`. | OpenClaw `install` hook installs `meshy-cli` from npm unpinned. Not for us. |

Findings:
- No file publishes, shares or sets visibility. The CLI commands in the recipes have no visibility flag. The Community page is not touched. The Pro ownership rule holds only if nobody publishes by hand in the web UI.
- Data that leaves the machine: prompts and input images or models, to Meshy only.
- Risk: `npm exec --yes` and `npx -y` run unreviewed npm code. Use a pinned global install by the owner, then call only `meshy`.
- Risk: an existing `MESHY_API_KEY` in the environment overrides the stored login. Check `meshy auth status` shows the Pro account (`source`).
- Risk: the skills do not know our credit caps. The agent must check `meshy balance` before and after each create, and ask before a second paid step.
- Answer to open question 3: the session file is `~/.config/meshy/credentials.json`. Device login uses the account that approves the code in the browser, so approve it with the Pro account.
- Verdict: no instruction to publish or exfiltrate. Safe to use with the rules in SKILL.md. Not pinned to a commit: the skills text can change, so re-read if the repo changes.
