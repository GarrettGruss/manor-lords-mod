"""Spike scenario (spec 29, part B): does a line of spawned cart actors stop a squad that walks through it?

A bandit squad starts START_GAP units east of a player squad and stands. The player squad walks east to attack it (the AI attacks on sight).
A line of props (default Resource_BigCart_C) is placed across the way. The scenario samples the bandit positions and records
how many unit sightings of the walking player squad were east of the line, inside the span of the props, and the closest approach of any unit to a prop.
Options: PROP (class key, default Resource_BigCart_C), PROP_COUNT (0 = control run), PROP_STEP (distance between props, game units).
"""

import math

from runlib import battle
from runlib.fights import START_GAP
from runlib.waiting import WaitTimeout

NAME = "probe-cart-block"
DESCRIPTION = "Spike: spawn a line of cart props between two squads and track whether the walking squad passes through."
COVERS: list[str] = []
LIMIT_S = 240
HIDDEN = True

TRACK_S = 14.0
POLL_S = 0.5
TRACK_SPEED = 3


class Track:
    def __init__(self, ctx, squad: int, props: list[dict], line_x: float, line_y: float):
        self.ctx, self.squad, self.props = ctx, squad, props
        self.line_x, self.line_y = line_x, line_y
        self.closest = float("inf")
        self.crossed = 0      # unit sightings east of the line, inside the span of the props
        self.samples: list[list[dict]] = []

    def __call__(self) -> bool:
        units = self.ctx.commands.send("squad_positions", squad=self.squad)["units"]
        self.samples.append(units)
        for unit in units:
            for prop in self.props:
                self.closest = min(self.closest, math.hypot(unit["x"] - prop["x"], unit["y"] - prop["y"]))
            if unit["x"] > self.line_x and abs(unit["y"] - self.line_y) < 250:
                self.crossed += 1
        return len(self.samples) >= TRACK_S / POLL_S


def run(ctx) -> dict:
    prop = battle.check_name("PROP", ctx.variant_option("PROP", "Resource_BigCart_C"))
    count = int(ctx.variant_option("PROP_COUNT", "5"))
    step = int(ctx.variant_option("PROP_STEP", "400"))
    ctx.actions.clear_battle()
    placed: list[dict] = []
    try:
        mover = ctx.actions.spawn_units("player", battle.SPEAR)
        squad = mover["answer"]["squads"][0]["id"]
        ctx.actions.spawn_units("bandit", "Brigands", dx=START_GAP)
        center = mover["answer"]["center"]
        line_x, line_y = center["x"] + START_GAP - 1000, center["y"]
        obstacles_before = ctx.commands.send("path_state")["obstacles"]
        if count > 0:
            span = (count - 1) * step
            placed = ctx.commands.send("prop_spawn", prop=prop, count=count, dx=START_GAP - 1000, dy=-span // 2, step=step)["placed"]
            ctx.log.info(f"props placed: {placed}")
        obstacles_after = ctx.commands.send("path_state")["obstacles"]
        ctx.log.info(f"path obstacles: {obstacles_before} before the props, {obstacles_after} after")
        ctx.metric("obstacles_before", obstacles_before)
        ctx.metric("obstacles_after", obstacles_after)
        track = Track(ctx, squad, placed, line_x, line_y)
        ctx.time.set_speed(TRACK_SPEED)
        try:
            ctx.run_until(track, TRACK_S + 30, what="the bandit track", poll_s=POLL_S)
        except WaitTimeout:
            ctx.log.info("track timed out")
        finally:
            ctx.time.pause()
        first, last = track.samples[0], (track.samples[-1] if track.samples[-1] else track.samples[len(track.samples) // 2])
        ctx.log.info(f"first sample: {first[:3]}")
        ctx.log.info(f"last sample: {last[:3]}")
        east = sum(1 for unit in last if unit["x"] > line_x + 100)
        ctx.metric("crossed_sightings", track.crossed)
        ctx.metric("units_last_sample", len(last))
        ctx.metric("units_east_of_line", east)
        ctx.metric("closest_to_prop", -1 if not placed else round(track.closest, 1))
        ctx.metric("samples", len(track.samples))
    finally:
        ctx.commands.send("prop_clear")
        ctx.actions.clear_battle()
    return ctx.result()
