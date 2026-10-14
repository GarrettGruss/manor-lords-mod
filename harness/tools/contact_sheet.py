"""Put PNG files side by side in one image, to review an art set at a glance.

Usage: uv run python harness/tools/contact_sheet.py OUT.png IN1.png IN2.png ... [--cell 200] [--columns 6]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--cell", type=int, default=200)
    parser.add_argument("--columns", type=int, default=6)
    args = parser.parse_args()
    label_height = 18
    rows = (len(args.inputs) + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (args.columns * args.cell, rows * (args.cell + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(args.inputs):
        x = (index % args.columns) * args.cell
        y = (index // args.columns) * (args.cell + label_height)
        with Image.open(path) as image:
            image.thumbnail((args.cell, args.cell))
            sheet.paste(image.convert("RGB"), (x, y))
        draw.text((x + 4, y + args.cell + 2), path.stem, fill="black")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
