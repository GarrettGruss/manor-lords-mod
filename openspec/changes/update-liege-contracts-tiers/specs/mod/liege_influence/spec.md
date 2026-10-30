## REMOVED Requirements
<!-- Issue: #533 -->

### Requirement: The liege screen has a button to request an arms shipment
**Reason**: The owner removed the arms shipment (decision 2026-10-30). The liege contracts replace it as the way to get weapons: a Medium contract can pay weapons.
**Migration**: None. The button, the command `InvasionMod.liege_request_arms`, the test command `liege_test_set_arms_day`, the config `liege_influence.arms_shipment` and the arms fields of `liege_state` are deleted. See the deletion tasks (section 4) of the change.

### Requirement: The arms shipment has a cooldown
**Reason**: The arms shipment is removed, so it has no cooldown.
**Migration**: The ModState key `arms_last_day` is no longer written. An old save that holds it loads without error, and the value is ignored.
