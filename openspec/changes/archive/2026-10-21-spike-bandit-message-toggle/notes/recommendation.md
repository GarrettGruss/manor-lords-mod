# Recommendation (task 1.5)

For the menu of #308 (the player sees only the mod button): use way 4, "detach the banner widget", as a small mod step after the mod sends the native letter.

- It is the only way that worked (run `s343-b1`; the other ways failed in c1, m1, m2 and e1). The reply letter itself cannot be stopped (native code, no hook sees it). The player does not need it, because the mod shows its own result.
- Take the list of live `questMessageElaborate_C` widgets before sending. Then poll about once a second after the send (the banner appears about 6 game seconds later), for at most about 20 game seconds. Hide only widgets that were not in the first list, so older quest banners stay.
- Residual risk: the reply letter stays in InBox (unopened, `wasOpened` false), so the game may still show a mailbox marker. Not checked.
- Alternative (not tried): replace the `DT_Para` reply rows with a pak. It changes data that the game uses everywhere, so it is worse for a player mod.

Owner decision (2026-10-21): hiding the banner is enough, and the letter may stay in InBox. Questions asked:
1. Is hiding the banner enough, or must the letter also leave InBox?
2. Is it fine that a banner of another quest message that appears in the same seconds may be hidden?

Next step if accepted: a mod command with the widget filter, a test scenario with a screenshot, then the change for #308.
