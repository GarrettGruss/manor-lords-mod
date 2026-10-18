# Design: Decide unattended regression run

## Open questions
| Question | Who decides | Notes |
|---|---|---|
| Run the `core` suite every night from a Windows scheduled task? | The user | The game needs an unlocked desktop session and the real window. The harness takes the screen and the mouse for `EXCLUSIVE` scenarios. |
| Use a second machine or user account for the game? | The user | It frees the user's screen. It needs a second game copy and the same safety rules for saves. |
| What happens on a failed night run: a file, a GitHub issue, or nothing? | The user | |

## Options
1. No schedule. The agent runs the suite before a pull request (today).
2. A scheduled task on this machine, at night, with `--max-minutes` and the run cap.
3. A second account or machine.
