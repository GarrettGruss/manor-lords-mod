# Esc key (task 2b)

## Question
How does Esc reach the game, and how can a mod menu close on Esc without the game's Esc menu opening?

## Findings
- UE4SS `RegisterKeyBind(Key.ESCAPE, fn)` fires (run 20261024-001206-171c, log "Esc pressed: closing the menu raid"). It does not swallow the key: the game also handles the same press.
- The game's Esc menu is the widget `mainMenu_widget_C` (the main menu widget, made on the first Esc and kept). Run 20261023-234808-12e8: before the first Esc no object exists. After it, `IsInViewport` is true and the visibility is 4 or 0. After the second Esc the visibility is 1 (Collapsed). The game pauses and hides the HUD while it is open.
- A Lua hook before a function cannot cancel the call. So the mod cannot stop the game's menu before it opens.
- Closing it again, run 20261024-001639-4d00 (picture per function): `widget:continue()` (the Continue button) collapses the menu and gives the HUD back (picture `after-continue.png`). `DoCloseAndHideSelf` collapses the widget but the HUD stays hidden. `unpauseAndResetDLSS`, `OnPauseMenuReopen` and `GoToPreviousMenu` do not close it.

## Decision
On Esc with a mod menu open, the base menu closes the menu (same path as the Close button, so the speed is restored) and watches for the game's Esc menu for 1.5 s. When it shows (visibility is not 1), the mod calls `continue` on it (fallback `DoCloseAndHideSelf`) and then restores the speed again, because the game's menu pauses the game. Without an open mod menu the mod does nothing, so Esc opens the game menu as before.

## Not verified
- The game's menu is on screen for 1 to a few frames before the mod closes it (a tick is 100 ms). A picture cannot show it.
- A held Esc key (key repeat) was not tested.

## Probes

`harness/scenarios/probe_esc_menu.py` (hidden test scenario `probe-esc-menu`) is the probe of this note: it presses Esc and calls each candidate function on the game menu widget.
