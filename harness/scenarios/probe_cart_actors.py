"""Spike scenario (spec 29, part B): which cart, wagon or siege classes are loaded and can be spawned?

For each candidate class path it calls the `spawn_probe` command (spawn our own actor high above the map, list its mesh components, destroy it).
Only classes that the game has already loaded can be found. It spawns nothing that the game owns and destroys only its own actor.
"""

from runlib.commands import CommandRefused

NAME = "probe-cart-actors"
DESCRIPTION = "Spike: spawns candidate cart, wagon and siege classes once each and logs their mesh components."
COVERS: list[str] = []
LIMIT_S = 180
HIDDEN = True

CANDIDATES = (
    "/Game/CPP_BP/Resources/Resource_BigCart.Resource_BigCart_C",
    "/Game/CPP_BP/Resources/Resource_Handcart.Resource_Handcart_C",
    "/Game/CPP_BP/Resources/Resource_TimberCart.Resource_TimberCart_C",
    "/Game/CPP_BP/Resources/Resource_Ladder.Resource_Ladder_C",
    "/Game/CPP_BP/BuildingMasterAssemble/BM_FoodCart.BM_FoodCart_C",
    "/Game/CPP_BP/BuildingMasterAssemble/BM_FirewoodCart.BM_FirewoodCart_C",
    "/Game/CPP_BP/BuildingMasterAssemble/BM_SiegeCamp.BM_SiegeCamp_C",
    "/Script/ManorLords.Obstacle",
)


def run(ctx) -> dict:
    spawned = 0
    for path in CANDIDATES:
        ctx.log.info(f"try {path}")
        try:
            answer = ctx.commands.send("spawn_probe", **{"class": path})
            ctx.log.info(f"spawned {path}: {answer}")
            spawned += 1
        except CommandRefused as error:
            ctx.log.info(f"refused {path}: {error.reason}")
    ctx.metric("classes_spawned", spawned)
    return ctx.result()
