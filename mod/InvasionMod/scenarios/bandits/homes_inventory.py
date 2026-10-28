"""Change update-banditry-rebellion-raid, task 2.1: read the inventory of every home and check the weapon id list.

A read only test scenario (it only stocks nothing). It lists which goods the homes of a fixture hold, which ids of
`rebellion_weapon_ids` appear, and how many families are valid. Run it on the fixtures `base`, `playtest-noai` and `base-corpse-pit`.
It saves nothing.
"""

NAME = "bandits-homes-inventory"
DESCRIPTION = "Reads the home inventories and the number of valid (armed) families. Task 2.1 of update-banditry-rebellion-raid."
LIMIT_S = 120


def run(ctx) -> dict:
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    ctx.log.info(f"HOMES families={homes['families']} housed={homes['housed']} valid={homes['valid']}")
    seen: dict[int, int] = {}
    for home in homes["homes"]:
        for row in home["inventory"]:
            seen[row["id"]] = seen.get(row["id"], 0) + row["amount"]
    ctx.log.info(f"HOMES goods by id {sorted(seen.items())}")
    ctx.notes.append(f"goods by id: {sorted(seen.items())}")
    ctx.notes.append(f"homes: {homes['homes']}")
    ctx.metric("families", homes["families"])
    ctx.metric("housed", homes["housed"])
    ctx.metric("valid", homes["valid"])
    weapon = set(homes["weapon_ids"].values()) if isinstance(homes["weapon_ids"], dict) else set(homes["weapon_ids"])
    ctx.metric("weapon_ids_seen", sum(1 for good in seen if good in weapon))
    ctx.check("the command listed the families", homes["families"] is not None and homes["families"] >= 1, homes["families"])
    return ctx.result()
