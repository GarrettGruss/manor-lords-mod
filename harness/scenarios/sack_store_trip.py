"""A raid trip takes goods from one named store; the loss per store is read (spec 10, spike S6, criterion R7)."""

from runlib import sack

NAME = "sack-store-trip"
DESCRIPTION = "Goods are removed from named stores with a loss factor. The per-store stock delta is read. Guard and lock are rules of the scenario."
COVERS = ["R7"]  # the base game has no guard or lock: they are modelled here by the loss factor. See criteria.json spike_note
LIMIT_S = 120

OPEN_BARN_LOSS_PCT = 50
GUARDED_GRANARY_LOSS_PCT = 10   # the loss of the open barn, reduced by a guard and a lock
TRIPS = 2
TOLERANCE_POINTS = 5.0          # each good is rounded on its own
MIN_STORES = 2                  # the base fixture has two stores with goods (two Supplies buildings)


def pick_stores(census: dict) -> tuple[dict, dict]:
    """The open barn (the smaller store) and the guarded granary (the larger store). A third store, if any, is left alone."""
    stores = sack.stores_by_size(census)
    if len(stores) < MIN_STORES:
        raise AssertionError(f"need {MIN_STORES} stores with goods, found {len(stores)}: {stores}")
    return stores[-1], stores[0]


def run(ctx) -> dict:
    expect = ctx.expect
    start = ctx.actions.sack_census()
    barn, granary = pick_stores(start)
    bystanders = [entry for entry in start["stores"] if entry["id"] not in (barn["id"], granary["id"])]
    ctx.notes.append(f"stores: barn {barn['id']} ({barn['goods']}), granary {granary['id']} ({granary['goods']}), others {[e['id'] for e in bystanders]}")
    expect.at_least("the granary holds more than the barn", granary["goods"], barn["goods"] + 1)

    for trip in range(1, TRIPS + 1):
        before = ctx.actions.sack_census()
        ctx.actions.sack_goods(percent=OPEN_BARN_LOSS_PCT, store=barn["id"])
        ctx.actions.sack_goods(percent=GUARDED_GRANARY_LOSS_PCT, store=granary["id"])
        after = ctx.actions.sack_census()
        barn_lost = sack.removed_share(sack.store(before, barn["id"])["goods"], sack.store(after, barn["id"])["goods"])
        granary_lost = sack.removed_share(sack.store(before, granary["id"])["goods"], sack.store(after, granary["id"])["goods"])
        expect.in_range(f"trip {trip}: open barn lost (percent)", barn_lost, OPEN_BARN_LOSS_PCT - TOLERANCE_POINTS, OPEN_BARN_LOSS_PCT + TOLERANCE_POINTS)
        expect.in_range(f"trip {trip}: guarded granary lost (percent)", granary_lost,
                        GUARDED_GRANARY_LOSS_PCT - TOLERANCE_POINTS, GUARDED_GRANARY_LOSS_PCT + TOLERANCE_POINTS)
        expect.at_most(f"trip {trip}: the guarded store loses less than the open one", granary_lost, barn_lost - 1)
        for other in bystanders:
            expect.equals(f"trip {trip}: store {other['id']} is untouched", sack.store(after, other["id"])["goods"], other["goods"])

    final = ctx.actions.sack_census()
    expect.equals("the stores are still standing", sack.standing(final), sack.standing(start))
    expect.at_most("stock fell", sack.stock_total(final), sack.stock_total(start) - 1)
    return ctx.result()
