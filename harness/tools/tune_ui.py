"""Streamlit page for live unit tuning (spec 28).

Start a game first: uv run python harness/run.py --scenario noop --keep-open
Then:               uv run streamlit run harness/tools/tune_ui.py -- --run <id>
Without --run the newest run with a commands folder is used.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))

from runlib.commands import CommandError  # noqa: E402
from runlib.tune import SIDES, STATS, TEMPLATES, TuneClient, export_preset, resolve_run  # noqa: E402

PRESET_DIR = ROOT / "docs" / "harness" / "28-unit-tuning" / "presets"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default=None, help="run id under runs/ (default: newest run with a commands folder)")
    return parser.parse_args(sys.argv[1:])


def guarded(action, *args):
    """Run one client call. Show the error on screen and return None when it fails."""
    try:
        return action(*args)
    except (CommandError, ValueError, OSError) as error:
        st.error(f"{type(error).__name__}: {error}")
        return None


def render_state(state: dict) -> None:
    st.subheader("State")
    rows = [{"side": side, "alive": row["alive"], **row["mean"]} for side, row in state["sides"].items()]
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No units with an owner found.")
    with st.expander("Squads"):
        st.dataframe([{"squad": s["squad"], "side": s["side"], "alive": s["alive"], **s["mean"]} for s in state["squads"]])
    st.caption(f"Units without owner: {state['unowned_units']}. Timer: {state['timer']}")
    st.write("Active overrides", state["overrides"] or "none")


def render_controls(client: TuneClient, state: dict) -> None:
    st.subheader("Overrides")
    means = {side: row["mean"] for side, row in state["sides"].items()}
    chosen: dict[str, dict[str, float]] = {}
    for column, side in zip(st.columns(len(SIDES)), SIDES):
        with column:
            st.markdown(f"**{side}**")
            for stat in STATS:
                current = float(means.get(side, {}).get(stat, 0.0))
                use = st.checkbox(f"set {stat}", key=f"use-{side}-{stat}")
                number = st.number_input(stat, min_value=0.0, max_value=1000.0, value=min(current, 1000.0), step=0.5,
                                         key=f"val-{side}-{stat}", label_visibility="collapsed")
                if use:
                    chosen.setdefault(side, {})[stat] = number
    apply_col, reset_col, refresh_col = st.columns(3)
    if apply_col.button("Apply checked values"):
        for answer in guarded(client.apply_values, chosen) or []:
            st.write(f"{answer['scope']} {answer['field']}={answer['value']}: {answer['changed']} writes, {answer['alive']} units")
    if reset_col.button("Reset all"):
        answer = guarded(client.reset)
        if answer:
            st.success(f"Removed {answer['removed']} overrides, restored {answer['restored']} values.")
    refresh_col.button("Refresh")


def render_spawn(client: TuneClient) -> None:
    st.subheader("Spawn test fight")
    left, right = st.columns(2)
    with left:
        player_template = st.selectbox("Player template", TEMPLATES, index=0)
        player_squads = st.number_input("Player squads", 1, 6, 1)
    with right:
        bandit_template = st.selectbox("Bandit template", TEMPLATES, index=3)
        bandit_squads = st.number_input("Bandit squads", 1, 6, 1)
    gap = st.number_input("Distance between the groups (game units)", 100, 5000, 1500, step=100)
    if st.button("Spawn test fight"):
        groups = [{"side": "player", "template": player_template, "count": int(player_squads), "dx": 800, "dy": 0},
                  {"side": "bandit", "template": bandit_template, "count": int(bandit_squads), "dx": 800 + int(gap), "dy": 0}]
        answers = guarded(client.spawn_fight, groups)
        if answers:
            st.success("Spawned: " + ", ".join(f"{a['units']} units" for a in answers))


def render_export(state: dict, run_id: str) -> None:
    st.subheader("Export")
    name = st.text_input("Preset name", value="preset")
    if st.button("Export overrides"):
        if not state["overrides"]:
            st.warning("There are no active overrides to export.")
        else:
            path = guarded(export_preset, state["overrides"], run_id, PRESET_DIR, name)
            if path:
                st.success(f"Wrote {path}")


def main() -> None:
    st.set_page_config(page_title="Unit tuning", layout="wide")
    st.title("Live unit tuning")
    run = guarded(resolve_run, ROOT / "runs", parse_args().run)
    if run is None:
        st.stop()
    st.caption(f"Run: {run.name}")
    client = TuneClient(run)
    state = guarded(client.state)
    if state is None:
        st.stop()
    render_state(state)
    render_controls(client, state)
    render_spawn(client)
    render_export(state, run.name)


main()
