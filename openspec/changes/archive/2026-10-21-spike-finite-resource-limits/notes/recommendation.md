# Recommendation (task 1.5)

Findings: the game has no region unlimited flag. The only reachable lever is the region production limit (`setProductionLimit`), which holds a high value (1000000) for a game day. The mine deposit (`amt` on the iron and salt clump, or `Ore.amt` in `deposits`) is not read yet.

Proposal for the later feature: set `setProductionLimit` of iron ore (14) and salt (145) to a large number and never call `setProductionUnlimited` for them. This is a limit on production, not a deposit, so it does not stop an infinite mine; it caps the output only.

Open points for the owner:
1. Provide a save with a built iron or salt mine (or approve a mouse-driven run to build one on a deposit), so that questions 1.1, 1.4 and the mine flag can be answered.
2. Decide if the production cap alone is acceptable as "large finite".

## Update 2026-10-22: salt mine session and owner decision

Live session with the owner (run 20261022-013541-4c3a, slot 0, `notes/salt-mine-deposit.md`):
- The owner built a salt mine (building type 7) in Nusslohe and assigned 3 families. The UI shows "Salt (Surface Deposit: 1194) / Rich Resource / Endless Underground Reserves".
- The surface deposit fell by 1 per game day with 3 families (1194 to 1190 over 4 days).
- The number exists only in the tooltip text (`MainUICPP_C.WidgetTree.WhiteTooltipRT`). No reflected field of the mine, its parts, the nearest `ResourceNode`, the region, the game manager or the pawn holds it. `RTSGameManager.deposits` is empty. So Lua cannot read the deposit from data or write it.
- The Nexus mod "Rich Deposit" (mod 357) sets deposits to rich with a native C++ DLL that patches game code; no source is published. This confirms that the deposit state lives in native code.

Owner decision (2026-10-22): accept that the mod cannot manage resource state (deposit amount, rich flag, endless reserves). The only lever that stays is the region production limit (`setProductionLimit` / `setProductionUnlimited`), which caps output and does not change a deposit.

## Update 2026-10-22: the IronClay lead

The Nexus Lua mod "IronClay" (May 2024) sets `bRichDeposit = true` on every `DepositDecal`. In today's game the class `DepositDecal` still exists (fields `bRichDeposit`, `depositedGood`, `Limit`, `depositType`), but no object of it exists, also after a game day (runs 20261022-024931-f585, 20261022-025607-3ef9). The 278 `Resource` actors are stone, fish, berries, mushrooms, eel, fallen trees and handcarts; none is a salt or iron deposit and none has a rich flag. So the IronClay route no longer works, and the owner decision stands. Details: `notes/deposit-decal.md`.
