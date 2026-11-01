## REMOVED Requirements
<!-- Issue: #552 -->

### Requirement: Vassals pay iron and salt as the permanent supply
**Reason**: The vassal tribute no longer has a fixed iron and salt part (change `update-vassal-tribute-rich-resources`). A vassal pays iron or salt only when it is a rich resource of its region (spec `mod/tribute`).
**Migration**: Remove `tribute.finite_goods`. The test scenario `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py` now checks that the tribute goods do not reduce a home deposit.
