# Recommendation (task 1.5)

Findings: the game has no region unlimited flag. The only reachable lever is the region production limit (`setProductionLimit`), which holds a high value (1000000) for a game day. The mine deposit (`amt` on the iron and salt clump, or `Ore.amt` in `deposits`) is not read yet.

Proposal for the later feature: set `setProductionLimit` of iron ore (14) and salt (145) to a large number and never call `setProductionUnlimited` for them. This is a limit on production, not a deposit, so it does not stop an infinite mine; it caps the output only.

Open points for the owner:
1. Provide a save with a built iron or salt mine (or approve a mouse-driven run to build one on a deposit), so that questions 1.1, 1.4 and the mine flag can be answered.
2. Decide if the production cap alone is acceptable as "large finite".
