# Evidence

Pictures of the probe `probe-raid-near` (game 0.8.117, fixture `playtest-noai`), compressed to 1208x720. The village belongs to a new AI lord at war with the player. A player militia squad (32 men) stands next to a built building of the lord.

| File | Run | Test scenario | What it shows |
|---|---|---|---|
| `skill-off-squad-next-to-building.jpg` | raidnear-13 (before-skill) | probe-raid-near, mode near, offset 0 | Squad before skill 19: no flame on the banner |
| `skill-on-240s-flag-false.jpg` | raidnear-13 (on-24) | same | 240 game s after `SetSkillActive(19, true, false)`: flame on the banner, squad still, no fire, no loot |
| `skill-on-180s-flag-true.jpg` | raidnear-7 (on-18) | same, flag true | Same with flag true |
| `skill-off-again.jpg` | raidnear-13 (off-4) | same | 40 game s after the skill is off: flame gone |
