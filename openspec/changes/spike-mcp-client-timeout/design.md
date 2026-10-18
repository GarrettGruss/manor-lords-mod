# Design: Spike MCP client timeout

## Open questions
| Question | Who decides | How it is answered |
|---|---|---|
| What is the real timeout of one MCP tool call in Claude Code? | A spike | Task 1.1: call a test wait of 30, 45, 60 and 90 s. |
| Is 45 s per `wait_for_run` call safe, with the hard cap of 50 s? | A spike | Task 1.2 |
| Does the setting differ by client version or by an environment variable? | A spike | Task 1.1 notes |
