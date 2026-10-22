## Why

Today the player picks the raid difficulty in the raid menu (F8) after the game started. The owner wants it set before the game starts, in the new game menu.

Owner decision (chat, 2026-10-21):

> "Order of the lord should be a mod setting added to the save game. I want this option to be configured before the game is started, and the new game menu. We could also reuse difficulty, i think the game has a built in raider difficulty slider we could read. The difficulty should also be tunable via the harness in game."

Issue: #358. Related: #340 (`add-raid-menu-actions`) and #308 (`add-mod-menu-access-rule`, its `core/menu.lua` clones game widgets).

## Assumptions (for owner review)

- The difficulty pick moves out of the raid menu (F8) into the game's new game menu. The raid menu keeps the `Difficulty` text line but loses the three buttons.
- The value is stored in the save with the mod state.
- If the game's own custom game settings have a raider or bandit difficulty or frequency setting, the mod reads that setting and does not add its own option.
- A harness named command sets the difficulty while the game runs. Today `invasion_pick_difficulty` does this, but only once.
- "Order of the lord" in the quote means the "Orders of the Lord" panel of the raid menu mockup, which held the difficulty buttons. The setting is the raid difficulty. Its name in the new game menu is open (task 2.3).

## What Changes

- Spike: find the new game settings of the game, test a mod option in the new game menu, test save and load of the value, and test a named command that sets the difficulty at any time.
- Behavior (after the spike, if it works): the difficulty is a new game setting stored in the save. Raid menu buttons are removed. The pick is no longer "once"; the harness can change it at any time.
- No code in this change folder. Spike tasks run later, in a game session.

## Impact

- Specs: `mod/raid_widget` (REMOVED: difficulty buttons), `mod/invasion` (MODIFIED: how the difficulty is set).
- Code (later): `mod/InvasionMod/Scripts/features/invasion/init.lua`, the raid menu feature, `core/menu.lua`.
- The spike result may change the delta specs. Update them in the same commit.
