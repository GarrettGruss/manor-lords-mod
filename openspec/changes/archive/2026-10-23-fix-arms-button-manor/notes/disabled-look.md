# Disabled look of the arms button

Choice (change fix-arms-button-manor, #455): a grey tint of the click button with `UserWidget:SetColorAndOpacity({R=0.4,G=0.4,B=0.4,A=1})`, and clicks ignored in `press()` while the rule says disabled. The enabled tint is white (1,1,1,1).

Why:
- `SetColorAndOpacity` on a click button widget is already in production in the tech tree widget (node colors), with no crash.
- `SetIsEnabled` was not tried: a Lua error inside a UObject call can crash UE4SS, and the click button is a Blueprint widget of our own pak (Button01 inside). A tint needs no pak change.
- The label stays "Request arms shipment". The reason shows in the arms info text under the button text lines, on a second line ("Build a manor first", "need 200 silver, 50 missing", "180 days left").
- The look is written once when the state changes (`S.arms_disabled`), not each refresh.

Manor reads:
- The first version read the building list (`manor_state`) at each refresh and at each `liege_menu_state` poll. Two real runs then crashed the game (access violation inside a UE4SS call, after the delivery and during the hover scan). A pass followed only after the fix below.
- Fix: the menu reads a cached manor answer. A built manor stays built while the menu is open. A missing manor is looked for again every 2 s. A click and the commands (`liege_state`, `liege_request_arms`) read the manor fresh.
- Evidence of the crash risk is two runs (20261024-025200-6707, 20261024-025737-e905) with the first version. The cause is not proven; the cache is a precaution that the later runs passed with.

Real runs (pak: the committed `mod/InvasionMod/paks/raidmenu_P.pak`; the work folder pak was older and had no ArmsButton, so the runs used a private work folder):
- new game, no manor: run 20261024-030921-798e passed (disabled look, reason shown, real click does nothing).
- default fixture with a built manor: run 20261024-030554-29b6 passed (enabled, real click delivers, cooldown look).
