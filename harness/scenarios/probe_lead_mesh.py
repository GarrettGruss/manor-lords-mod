"""Probe for lead 1.5 (building mesh swap) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite. Run on a fixture with finished buildings (the default one):
    uv run python harness\\run.py --scenario probe-lead-mesh --slot auto
The probe lists the mesh components of buildings, picks one component and a mesh of a different building, swaps the mesh with
SetStaticMesh, records mesh, bounds, collision flag and socket count before and after, takes a screenshot, and restores the
old mesh. It reads socket counts only; it passes no socket name to the game. It never calls a save function.
"""

from runlib.leadprobe import Probe

NAME = "probe-lead-mesh"
LIMIT_S = 200
HIDDEN = True


def pick_pair(components: list):
    """A component and the mesh path of a component with another mesh. (None, None) when all meshes are equal."""
    for target in components:
        for other in components:
            if other["mesh"] and target["mesh"] and other["mesh"] != target["mesh"]:
                return target, other["mesh"]
    return None, None


def run(ctx) -> dict:
    probe = Probe(ctx)
    listing = probe.attempt("mesh list", ctx.actions.lead_mesh_list)
    components = (listing or {}).get("components", [])
    probe.metric("components", len(components))
    target, new_mesh = pick_pair(components)
    if not target:
        probe.note("no pair", reason="need two building components with different meshes")
        return ctx.result()
    ctx.screenshot("mesh-before")
    swapped = probe.attempt("swap", lambda: ctx.actions.lead_mesh_swap(target["full"], new_mesh))
    ctx.time.run_game_seconds(2, speed=1)
    ctx.screenshot("mesh-after")
    if swapped and swapped.get("ok"):
        before, after = swapped["before"], swapped["after"]
        probe.metric("swap_ok", 1)
        probe.metric("mesh_changed", before["mesh"] != after["mesh"])
        probe.metric("collision_same", before["collision"] == after["collision"])
        probe.metric("sockets_before", before["sockets"])
        probe.metric("sockets_after", after["sockets"])
        extent_before, extent_after = before.get("extent"), after.get("extent")
        if isinstance(extent_before, dict) and isinstance(extent_after, dict):
            probe.metric("extent_x_before", extent_before["x"])
            probe.metric("extent_x_after", extent_after["x"])
    else:
        probe.metric("swap_ok", 0)
    probe.attempt("restore", lambda: ctx.actions.lead_mesh_swap(target["full"], restore=True))
    return ctx.result()
