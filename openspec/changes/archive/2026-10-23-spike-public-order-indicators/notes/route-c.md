# Route C: a pak (task 4.1)

**Not needed and not built.** The change says route C is for the case that A and B fail. Route B gives a custom row from Lua.

Facts for the record (static, from #403 and the asset of this spike):

- A pak cannot add a factor: `EApprovalFactorType` is a native enum of 34 values.
- The row text comes from `DT_Translation_Approval` through `getTranslatedTextFromDataTable` (name list of `approvalFactorWidget`). The label of an enum value is a row of that table. A pak could change the **text** of a native label (for example the label of `unburied` to "Bandit fear"). That would change it for the real meaning too, so it is not a good route. Not tried.
- A pak could replace the widget `BigTooltip_ApprovalAndPublicOrder` or `approvalFactorWidget` (a cooked widget Blueprint). Route B shows that Lua is enough, so the cost of a cooked widget is not justified.
