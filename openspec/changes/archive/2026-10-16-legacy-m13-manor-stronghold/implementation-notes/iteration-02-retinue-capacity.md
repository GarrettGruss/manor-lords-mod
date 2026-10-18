# Iteration 02: retinue capacity

- Fixture `manor-bailey`: a built manor house. Start: 5 bound retinue, limit 12, hire cost 50 silver.
- Without a hook: 7 hires reach 12, then `canHireRetinue` is false and `hireExtraRetinue` adds nothing.
- With a `getModularGarrisonLimit` hook (+24): scripts read 36. `canHireRetinue` (called by script) is still false at 12, hires stop at 12. So the native `canHireRetinue` and `hireExtraRetinue` use native values.
- With a `canHireRetinue` hook that returns true below the raised limit: the gate is true (what a Blueprint caller sees), but `hireExtraRetinue` still adds nothing at 12. The refusal is inside the native hire.
- Consequence for the design: "larger retinue" cannot be reached by hooks alone. Options for later: extra retinue squads, a mod-owned hire, or a native patch (LargerFormations style, out of scope: a DLL).
- Hook limit: native C++ callers are not changed.
