# Carry caps: defaults and the raid type source

## Raid type source (task 1.2)

`design.md` gives no recommendation, so this is the smallest choice that fits the spec.
The tracker derives the raid type from data it has already (`rules.raid_type`):

- a lord army (`raid.lord` set) is `hussite`;
- bandit squads of a role raid (`raid.roles`, no lord) are `bandit`;
- a native raid (`spawnRaiders`) has no known type and uses `carry_cap`.

Reason: no change in the invasion feature or in the spawn info is needed, and a raid with no known type keeps the old cap, as the spec says.

## Defaults (PROVISIONAL)

The real-game spike (task 1.1) has not run. The values are from `design.md` and M00 and may change after the spike.

| Raid type | Config key | Value |
|---|---|---|
| hussite | `raid_behavior.carry_caps.hussite` | 10 |
| bandit | `raid_behavior.carry_caps.bandit` | 5 |
| unknown | `raid_behavior.carry_cap` | 10 |

A cap by good (grain 10, iron 5) is not built: the spike must first show if `ItemsLooted` has a good.
