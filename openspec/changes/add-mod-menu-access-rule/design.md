# Design: Add mod menu access rule

## Decisions
- The rule counts clicks from the normal game view with no mod menu open, to the root menu shown on screen.
- One shared entry point is allowed: for example one "Mod" button that opens a small list of mod menus (click 1), then the menu (click 2).
- Keys stay as shortcuts. The rule only forbids a menu that needs a key.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | Where is the entry point: a new HUD button, or a button inside an existing game menu? Can a pak or Lua add a HUD button at all? | A spike, then the owner | Task 1.1 |
| 2 | One shared "Mod" button, or one button per menu? | Owner | Owner reply after task 1.1 |
