"""Build, burn and rebuild a Dunghill, and read the goods that each construction site needs (spec 10, spike R8, criterion R8).

It uses the real OS mouse (action place_building), so it is hidden. Run it alone on a computer that nobody is using:
    .venv\\Scripts\\python.exe harness\\run.py --scenario rebuild-cost
The game window must be visible.
"""

NAME = "rebuild-cost"
DESCRIPTION = ("Place a Dunghill with the real mouse and read its cost (4 Planks). Build it, burn it (Rubble), demolish the ruin, place it again: "
               "the base game asks the full cost. Lower the cost of the new site to half: the builders use half. Proves that the cost "
               "can be read and lowered, and that a rebuild happens; the mod defines the discount.")
COVERS = ["R8"]
# Hidden on purpose: place_building takes over the real mouse and the keyboard focus.
HIDDEN = True
LIMIT_S = 240
DUNGHILL = 121
PLANKS = 17
RUBBLE = 75
SPEED = 3
STEP_GAME_SECONDS = 40   # one game day
MAX_STEPS = 8
STOCK_PLANKS = 60
COST_RANGE = (1, 20)     # seen: 4. Far outside means a wrong read.


def planks(ctx) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [PLANKS, False, False])


def site_cost(ctx) -> int:
    """Planks that the one construction site of the Dunghill still needs. Fails the run if the site lists other goods."""
    answer = ctx.actions.building_sites(DUNGHILL)
    sites = [row for row in answer["buildings"] if not row["built"] and not row["rubble"]]
    ctx.expect.equals("one Dunghill construction site", len(sites), 1)
    needs = {need["good"]: need["amount"] for need in sites[0]["needs"]} if sites else {}
    ctx.expect.equals("the site needs only Planks", sorted(needs), [PLANKS])
    return needs.get(PLANKS, 0)


def run_steps_until(ctx, what: str, done) -> bool:
    for _ in range(MAX_STEPS):
        ctx.popups()
        if done():
            return True
        ctx.time.run_game_seconds(STEP_GAME_SECONDS, speed=SPEED)
    ctx.expect.record(what, done(), "not reached", f"within {MAX_STEPS} game days")
    return done()


def dunghill_built(ctx) -> bool:
    return ctx.actions.building_sites(DUNGHILL)["counts"]["built"] == 1


def fire_is_out(ctx) -> bool:
    ruins = ctx.actions.building_sites(RUBBLE)["buildings"]
    return len(ruins) >= 1 and not any(row["burning"] for row in ruins)


def build_and_check_use(ctx, label: str, expected_use: int) -> None:
    before = planks(ctx)
    run_steps_until(ctx, f"{label}: the Dunghill is built", lambda: dunghill_built(ctx))
    used = before - planks(ctx)
    ctx.expect.in_range(f"{label}: planks used by the builders", used, expected_use, expected_use)


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.give_item("planks", STOCK_PLANKS)

    ctx.actions.place_building(DUNGHILL)
    full_cost = site_cost(ctx)
    expect.in_range("full cost in planks, read from the site", full_cost, *COST_RANGE)
    build_and_check_use(ctx, "first build", full_cost)

    ctx.actions.ruin_building(DUNGHILL, method="fire")
    run_steps_until(ctx, "the fire is out", lambda: fire_is_out(ctx))
    ruins = ctx.actions.building_sites(RUBBLE)["buildings"]
    expect.equals("the burned building is rubble (type 75)", [row["type"] for row in ruins], [RUBBLE])
    expect.equals("no Dunghill stands", ctx.actions.building_sites(DUNGHILL)["counts"]["built"], 0)

    ctx.actions.demolish_ruins()
    ctx.actions.place_building(DUNGHILL)
    rebuild_cost = site_cost(ctx)
    expect.equals("base game: the rebuild asks the full cost", rebuild_cost, full_cost)

    discounted = max(1, full_cost // 2)
    ctx.actions.set_site_cost(DUNGHILL, PLANKS, discounted)
    expect.equals("the site shows the lower cost", site_cost(ctx), discounted)
    build_and_check_use(ctx, "rebuild with a discount", discounted)

    ctx.metric("full_cost_planks", full_cost)
    ctx.metric("discounted_cost_planks", discounted)
    return ctx.result()
