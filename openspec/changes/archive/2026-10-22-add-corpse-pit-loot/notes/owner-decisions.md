# Owner decisions (2026-10-22)

- Option (a) for Hussite raids only. A native raid gets no loot give-back.
- The plunder tick records the goods per raid. Each body gives its share into the pit.
- Share = floor(goods / raiders at the start). The remainder is lost.
- Pit deliveries from bodies the mod does not know are ignored.

# Implementation notes

- Each dead Hussite raider adds 1 to `raid.unpaid` (`rules.note_deaths`). A departure is not a death. A rise of the pit corpse count pays at most `unpaid` shares, oldest raid first.
- The poll runs only after a Hussite raid exists; the first look sets the baseline, so earlier bodies are not counted.
- The record is kept in memory and shown in the ModState text key `raid_plunder_record` (latest raid). Raids themselves are not restored after a load, so "the record survives a load" is not checked yet.
- `world.plunder` now returns the goods by type as a second result.
