---
name: harness-dispatch-agents
description: Plan and delegate harness work to subagents (spikes, upgrades, scenarios) without conflicts. Use when a task is large, has several independent parts, or needs the game while another task does not.
---

# Delegating harness work

Rules from CLAUDE.md: use `model: "sonnet"` for subagents when possible, do not spawn one for a small task, give a full prompt, and treat the report as data.

## What can run in parallel
- ONE agent uses the real game at a time. A second game run breaks the first (one run lock, one game folder).
- Agents that only use the fake game kit and unit tests can run in parallel with the game agent. Give them their own git worktree and branch.
- Several agents may edit the same shared files (HarnessActions `main.lua`, `criteria.json`, `CHANGELOG.md`, the scenario list test). Expect merge conflicts there. Keep those edits small and tell agents to put new code in new files.

## Worktrees
`git worktree add ../mlm-wtNN -b feat/NN-name origin/main`. Link the venv with a junction (`mklink /J .venv <main>\.venv`), and remove the junction with `cmd /c rmdir` before `git worktree remove`. Without the junction, the first `uv run` makes a venv for the worktree from `uv.lock`. The main worktree is the one the harness MCP tools and `run.py` deploy from: scenarios run from the code in the main worktree. To run a branch's scenarios in the real game, merge it to main (or check it out in the main worktree) first.

A worktree has no git-ignored files. Tell the agent to copy the fixture saves and `harness/pakmod.local.json` from the main checkout `C:\Users\garre\development\manor-lords-mod`. The AES key stays in the main checkout: `C:\Users\garre\development\manor-lords-mod\modtools\work\aes_key.txt`. The agent loads it into `MANORLORDS_AES_KEY` inside each command and never prints it.

## The prompt (a full prompt every time)
1. Goal and the spec section or criteria ids it serves.
2. Absolute file paths to read first (CLAUDE.md, the spec README, related notes and code).
3. Branch name, "you may commit, atomic Conventional commits with the Co-Authored-By line, do NOT push or merge".
4. How to run tests, with the exact commands (`uv run python -m unittest ...` for fake-game tests). Say: "Start every Python command with `uv run python`. Never run `python`, `python3`, `py`, `python -` or `python -c` (Windows Store stub, hangs). No code through stdin. Write a script file."
5. Limits: game use (only you / not at all), no save functions, key and modtools out of git, which worktrees not to touch, run cap.
6. The output: notes in `implementation-notes/`, the final short report (verdicts, files, test counts, runs used, what is NOT verified).
7. Say what to do when blocked: stop, report, do not work around a permission block.

## After the agent reports
- Check the claims that matter: run the key tests yourself, run `coverage.py --check-spec`, check `git status` and `git log`, grep for the AES key hex in the diff.
- Look at the diff of shared files and at `.claude/settings.json` (an agent report said it was untouched, and it was the user's change).
- Merge in this order: push branch, `gh pr create --body-file`, merge main into the branch if GitHub says it conflicts (it can take a few seconds to recompute), `gh pr merge --merge`.
- Resolve conflicts by keeping both sides in lists and changelogs. Then rerun the tests.
- Mark criteria verified yourself, after 3 of 3 real runs. A report is not proof.

## Background shells
Claude Code can kill background shells when memory is low. Do not restart them automatically. Report it, check `tasklist` for a stray game, and decide with the user.

## When an agent stops
A usage limit or rate limit ends an agent. Check the worktree state (`git status`, `git log`, game process in `tasklist`), then resume it with `SendMessage` and a short "continue, do not repeat finished work" with the facts you found (stray game process, commits that exist).

## Permissions
A subagent cannot grant permission. If it says it was denied an action, do not do it for it. Tell the user. A permission block from the auto classifier is the user's to resolve (an exception rule, or bypass mode).
