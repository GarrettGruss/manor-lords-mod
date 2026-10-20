---
name: harness-meshy-agent
description: Use the Meshy 3D agent CLI (meshy-cli and the meshy-3d-generation skill) for Meshy modes that genmesh.py lacks, then feed the result into the harness-meshy import and pak steps. Use only after the owner has installed it by hand.
---

# Meshy 3D agent pipeline

Review of the source: `install-review.md`. Read it first.

## IMPORTANT: Meshy Pro account and private ownership (owner, 2026-10-19)
We use a Meshy **Pro** account. Its license for the models we generate:
- Ownership: full private ownership. Commercial use: allowed, with full commercial rights. Attribution: not required.
- Condition: we keep private ownership only if we do NOT publish the models to the Meshy Community page, and our input assets (prompts, reference images) do not violate third-party copyrights.
- So: never publish, share or make public a model on the Meshy Community page. Keep task visibility private. Use only our own or licensed input images.

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

## Commands for a house (CLI 0.4.3, reviewed in `install-review.md`)
The CLI has no visibility or publish flag. Tasks stay private in the account. Never publish in the web UI.
Run every command separately and read its JSON. `WORKSPACE` is `runs/genmesh/<name>`.

1. Check balance: `meshy balance --output-schema v1 --format json --no-update-check`
2. Image-to-3d house (best, from a Gemini reference image of our own; untextured geometry first, fewer credits; the grey material rule applies later):
   `meshy image-to-3d create --image-url "runs/genmesh/<name>/ref.png" --model-type standard --should-texture false --target-formats glb --async --output-schema v1 --format json --no-update-check`
   Reference must be PNG or JPG. Low poly option: `--model-type smart-topology --target-polycount 10000` instead of `--model-type standard`.
3. Text-to-3d house: `meshy text-to-3d create --mode preview --prompt "<house description>" --target-formats glb --async --output-schema v1 --format json --no-update-check`
4. Read `result.submission.task_id` as `TASK_ID`, then:
   `meshy project init --root "runs/genmesh/<name>" --name "<name>" --task-id TASK_ID --task-type image-to-3d --workspace "runs/genmesh/<name>" --output-schema v1 --format json --no-update-check`
   `meshy image-to-3d wait TASK_ID --timeout 600 --project "PROJECT_DIR" --stage geometry --workspace "runs/genmesh/<name>" --output-schema v1 --format json --no-update-check`
   (`PROJECT_DIR` is `result.project_dir` of the init result. For text-to-3d use `text-to-3d` and `--stage preview`.)
5. Optional FBX: `meshy convert create --input-task-id TASK_ID --target-formats fbx --async --project "PROJECT_DIR" --stage convert --workspace "runs/genmesh/<name>" ...` then `wait` through `convert`. GLB is the default and is enough for the harness-meshy import.
6. Download: `meshy download --task-json "PROJECT_DIR/task_TASK_ID.json" --model-format glb --output "runs/genmesh/<name>/model.glb" --project "PROJECT_DIR" --stage delivered --workspace "runs/genmesh/<name>" --output-schema v1 --format json --no-update-check`
   Check the output name against what `genmesh.py` writes in that folder. Add `--overwrite` only on purpose.
7. Check balance again. Record task id and credits (`consumed_credits`) in `notes/meshy-assets.md`.
Cost: the CLI has no price command for create steps except `meshy make "<text>" --dry-run`; use https://docs.meshy.ai/en/api/pricing.

## Keys and secrets
- Never commit or write an API key, a token or the CLI session file in the repo.
- Meshy output is shipped under the Pro plan terms quoted in `harness-meshy`.

## Links
- `harness-meshy`, `harness-pak-mod`
- Wiki: `docs/wiki/workflows/meshy-models.md`
- Source repo: https://github.com/meshy-dev/meshy-3d-agent
