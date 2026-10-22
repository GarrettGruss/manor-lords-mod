# Message source (task 1.2)

Result: the banner is the widget class `questMessageElaborate_C` (`/Game/UI/Elements/questMessageElaborate`). The reply letter is made by native code.

Evidence (run `s343-h1`, hooks on 16 functions, all registered except one duplicate):
- `PawnCPP:sendLetter` fired once with `["raider_suggestSettle+30"]` (the call of the mod).
- Hooks silent for the reply: `PawnCPP:addToInbox`, `playEventMessage`, `playMessage`, `playEventComplexMessage`, `playQuestMessage`,
  `issueRaiderTrackingQuestIfNew`, `pickVoiceResponse`, `changeRelationTags`, and the Blueprint functions `playQueuedEventMessage`, `playPopupMessage`,
  `LetterOpenedEventHandler`. So the reply letter and the banner are made inside native code, below the hook level (ProcessEvent).
- Fired often, but not the cause: the Blueprint timers `MyPawnCPP_BP3_C:displayNewDiplomaticMessages` and `checkInbox_Timer` (once a second, 97 and 96 events),
  `playVoiceResponse` (unit voice lines), `QuestMessage` (once, for the hidden start quest `victory_growth`).
- Widget counts (runs `s343-e1`, `s343-b1`): `questMessageElaborate_C` 1 before the letter and right after it, 2 at +6 s. The class fits the banner look (title "A New Message", letter icon, number).
- Letter struct (jmap): `Guid, paras, daySent, sender, senderSetupIndex, recipient, recipientSetupIndex, read, wasOpened`. `PawnCPP:changeLetterRead(letterToChange, bLetterRead)` exists.

Not found: the exact native function that makes the banner. Not tried: a hook on the widget `Construct` event (would show the caller).
