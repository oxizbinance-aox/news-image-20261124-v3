#!/usr/bin/env python3
"""Density counter gate for the NI24 v3 entry.

Reads manifest.json (written by draw_news24.py from the same story data that
is drawn) and entry.png, and verifies the hard gates: >=30 stories (cap 42),
6-9 regions, world map present (ink check on the map zone), >=2 charts
(region bars + markets bars + the line chart in lead 1), a data strip
(big red numbers present), 1024x1024 and <=1 MiB. Prints the numbers and
exits non-zero on any failure. Tesseract is not installed on this machine,
so story presence is verified from the manifest plus a pixel-ink check that
each zone of the image actually carries drawn content.
"""
import json
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent


def zone_ink(img, box):
    """Fraction of pixels in box that differ from plain paper."""
    crop = img.crop(box).convert("L")
    px = list(crop.getdata())
    dark = sum(1 for p in px if p < 225)
    return dark / max(1, len(px))


def main():
    fails = []
    man = json.loads((HERE / "manifest.json").read_text())
    stories = man["stories"]
    regions = man["regions"]
    charts = man["charts"]
    img = Image.open(HERE / "entry.png")
    size = (HERE / "entry.png").stat().st_size

    print(f"DENSITY COUNT: stories={stories} regions={regions} "
          f"charts={charts} map={man['map']} "
          f"timeline={man['timeline_events']} numbers={man['numbers']}")
    print(f"IMAGE: {img.size[0]}x{img.size[1]} {size} bytes")

    if not 30 <= stories <= 42:
        fails.append(f"stories {stories} outside 30-42")
    if not 6 <= regions <= 9:
        fails.append(f"regions {regions} outside 6-9")
    if charts < 2:
        fails.append(f"charts {charts} < 2")
    if not man["map"]:
        fails.append("map missing")
    if img.size != (1024, 1024):
        fails.append(f"size {img.size} != 1024x1024")
    if size > 1048576:
        fails.append(f"file {size} bytes > 1 MiB")

    # ink checks: each zone must carry real drawn content
    checks = [
        ("map zone", (8, 704, 568, 816), 0.05),
        ("region chart zone", (576, 704, 1016, 780), 0.01),
        ("markets chart zone", (576, 780, 1016, 816), 0.01),
        ("numbers strip", (8, 150, 1016, 196), 0.01),
        ("lead banners", (8, 221, 1016, 321), 0.20),
        ("pictures strip", (8, 938, 1016, 978), 0.20),
    ]
    for name, box, floor in checks:
        ink = zone_ink(img, box)
        print(f"INK {name}: {ink:.3f} (floor {floor})")
        if ink < floor:
            fails.append(f"{name} ink {ink:.3f} < {floor}")

    # the numbers strip must contain big red figures
    strip = img.crop((8, 150, 1016, 196)).convert("RGB")
    reds = sum(1 for r, g, b in strip.getdata() if r > 140 and g < 90 and b < 90)
    print(f"NUMBERS STRIP red pixels: {reds}")
    if reds < 200:
        fails.append("numbers strip has no big red figures")

    if fails:
        print("DENSITY GATE: FAIL")
        for f in fails:
            print(" ", f)
        return 1
    print("DENSITY GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
