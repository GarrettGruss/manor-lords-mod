## Decisions

- Reuse `core.settle_region` with the player pawn on the player region, `families_per_call = 5` and the camp spot finder of the refugees feature. The player owns its region, so the guard in `ManorCore` passes. To avoid duplicate code, the camp spot function moves to a shared place or is called through the refugees world module.
- New families are homeless families in a tent camp. This is what `settleRegion` does. The game moves them into houses when houses exist.
- Calls needed: `ceil(missing / 5)`. If the result is more than 10 families, the mod removes the extra last families. The final count is read with `getTotalNumFamilies()`.
- Removal keeps the existing path: `just_die` on each living member of the last families.
- If the count cannot be reached, the mod logs a warning and keeps the state. The flag is still set (no retry loop).
- The test reports both the family count and the people count. The people count is not asserted exactly.
