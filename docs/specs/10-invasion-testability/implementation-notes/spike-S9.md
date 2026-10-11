# Spike S9: a countdown text in the UI (criterion T4)

Date: 2026-10-10. Game: real game, base fixture. Tools: bridge eval (approved for experiments), then the command `show_message` of `HarnessActions` version 10.
Verdict: **the test method works.** A mod can show a text with a number, update it, and the harness reads the text back from the widget. A screenshot shows it.
T4 stays mark P: the harness proves the text and the picture. A person judges how it looks (Q4 stays human).

## Question
Can Lua show a countdown or warning text ("Raid in N days") without a pak, and can the harness read it back?

## What was found
- `PawnCPP:playEventMessage(msgType: Name, primaryText: String, secondaryText: String)` works from Lua.
  The first argument must be an `FName`. A plain string crashes the game (this was the cause of the old crash in the actions catalog).
  `FName("Default")` works. The call returned `nil` and made no crash in 6 manual calls and 9 scenario calls.
- The call creates one widget `genericAchievement_EventMessage_C` (parent `BP_MLGameInstance_C`). It is the banner at the top of the screen:
  a dark ribbon with the big text, the second line below it. The screenshot shows "Raid in 2 days" (`runs/ui-countdown-3/screenshots/countdown-2.png`).
- Read back: the widget properties `Text` and `textSecondary` (Text) and the text blocks `main_txt:GetText()` and `bottomTxt:GetText()`
  hold the strings. Also `msgType` (Name), `animFinished` (bool), `atTheTop?` (bool).
- Old banners stay in memory after they fade (two widgets at once were seen). The mod finds the new widget by comparing the widget names
  before and after the call. `IsInViewport` was false for a visible banner, so it is not used (same as the pop-up widget in spike S8).
- `playFeedbackTextFunction(Text, Pos, PlaybackSpeed)` (floating text), `playPopupMessage(messageType Name, Region)` (the hunger and cold pop-ups; types come from
  `DT_Popups`) and `spawnTutorialMessage` exist. They were not needed and not tried. `playPopupMessage` pauses the game, so it is a bad fit for a countdown.
- The banner appears while the game is paused (the screenshot shows "Game Paused" under it) and while it runs.

## Method in the harness
- `mod/shared/HarnessUi` and the commands `show_message`, `read_message`, `list_messages` in `HarnessActions`. The text is checked: letters, digits, space and `, . ! : -`, at most 60 characters (80 for the second line).
  No raw Lua. The Python action `ctx.actions.show_message(text, subtext)` checks the same rules and the read-back, and `read_message()` and `list_messages()` read.
- Scenario `ui-countdown` (COVERS T4): write `daysUntilNextRaid` = 4, show "Raid in N days" with N read from the timer, read the widget text back, take a screenshot,
  run one game day at 8x, and show the new N. N is 4, 3, 2. It stops before the day that brings the timer to 0. A text with markup characters is refused.

## Results
Scenario `ui-countdown`, real game, 3 of 3 passed: `ui-countdown-1`, `ui-countdown-2`, `ui-countdown-3` (about 63 s each, 3 screenshots each).
Each run: the text read back equals "Raid in N days" for N = 4, 3, 2 (widget `Text`, text block, and second line).

## Not verified
- How the banner looks to a player (size, colour, how long it stays, readability on other resolutions). That is Q4, a human judgment.
- The banner fades after a few seconds. A permanent countdown needs a repeat call (for example once for each game day) or a custom widget. A custom widget from Lua was not tried.
- Message types other than `Default`. Localization of the text (the strings are shown as given).
- The mod that really announces raids (spec 10, upgrade U7) has to call the same function. The method is proven, not the mod.
