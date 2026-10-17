"""Spike 11: build slot folders and start several games at the same time.

  uv run python harness/tools/spike11_slots.py build --slots 1 2
  uv run python harness/tools/spike11_slots.py run --label two-low --slots 0 1 --settings low

Slot 0 is the normal game folder. Slot <n> is slots/<n>/Manor Lords/:
- Win64 is a full copy (exe, UE4SS, mods), so each slot has its own mods.
- Content/Paks is a real folder with hard links to the game paks, so each slot has its own ~mods folder.
- Engine, Plugins, Content/Movies and Content/Slate are junctions to the game folder (read only data).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GAME_ROOT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords")
SLOTS_ROOT = REPO_ROOT / "slots"
WORKER = Path(__file__).resolve().parent / "spike11_worker.py"
JUNCTIONS = ("Engine", "ManorLords/Plugins", "ManorLords/Content/Movies", "ManorLords/Content/Slate")


def slot_root(slot: int) -> Path:
    return GAME_ROOT if slot == 0 else SLOTS_ROOT / str(slot) / "Manor Lords"


def junction(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)


def build_slot(slot: int) -> None:
    root = slot_root(slot)
    if root.exists():
        raise SystemExit(f"slot {slot} exists already: {root}")
    for relative in JUNCTIONS:
        junction(root / relative, GAME_ROOT / relative)
    win64 = "ManorLords/Binaries/Win64"
    # robocopy exit codes below 8 mean success.
    copy = subprocess.run(["robocopy", str(GAME_ROOT / win64), str(root / win64), "/E", "/NFL", "/NDL", "/NJH", "/NJS"])
    if copy.returncode >= 8:
        raise SystemExit(f"robocopy failed with code {copy.returncode}")
    paks = root / "ManorLords/Content/Paks"
    paks.mkdir(parents=True)
    for source in (GAME_ROOT / "ManorLords/Content/Paks").iterdir():
        if source.is_file():
            (paks / source.name).hardlink_to(source)
        elif source.name == "LogicMods":
            subprocess.run(["robocopy", str(source), str(paks / source.name), "/E", "/NFL", "/NDL", "/NJH", "/NJS"])
    print(f"slot {slot} built at {root}")


def gpu_used_mb() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().splitlines()[0])


# Tiles of 1280x720 on the 2560x1440 screen. Slot n gets tile n, so windows do not cover each other.
TILES = ((0, 0), (1280, 0), (0, 720), (1280, 720))


def window_args(slot: int) -> str:
    return f"-windowed -ResX=1280 -ResY=720"


def run_games(label: str, slots: list[int], settings: str, tile: bool) -> dict:
    gpu_samples: list[int] = []
    stop = threading.Event()

    def sample_gpu() -> None:
        while not stop.is_set():
            gpu_samples.append(gpu_used_mb())
            time.sleep(2)

    gpu_before = gpu_used_mb()
    sampler = threading.Thread(target=sample_gpu, daemon=True)
    sampler.start()
    workers = []
    for slot in slots:
        run_dir = REPO_ROOT / "runs" / f"spike11-{label}-slot{slot}"
        command = ["uv", "run", "python", str(WORKER), "--slot-root", str(slot_root(slot)), "--run-dir", str(run_dir),
                   "--settings", settings, "--hold", "30",
                   "--game-args", window_args(slot) if tile else ""]
        if tile:
            command += ["--tile", *map(str, TILES[slot])]
        workers.append(subprocess.Popen(command, stdout=subprocess.PIPE, text=True, cwd=REPO_ROOT))
    results = [json.loads(worker.communicate()[0].strip().splitlines()[-1]) for worker in workers]
    stop.set()
    return {"label": label, "slots": slots, "settings": settings, "gpu_before_mb": gpu_before,
            "gpu_peak_mb": max(gpu_samples, default=None), "games": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "run"))
    parser.add_argument("--slots", type=int, nargs="+", required=True)
    parser.add_argument("--label", default="spike")
    parser.add_argument("--settings", choices=("low", "low-live", "user"), default="low")
    parser.add_argument("--tile", action="store_true", help="start each game windowed at 1280x720 in its own screen tile")
    args = parser.parse_args()
    if args.command == "build":
        for slot in args.slots:
            if slot == 0:
                sys.exit("slot 0 is the game folder, it is not built")
            build_slot(slot)
        return
    result = run_games(args.label, args.slots, args.settings, args.tile)
    out = REPO_ROOT / "runs" / f"spike11-{args.label}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
