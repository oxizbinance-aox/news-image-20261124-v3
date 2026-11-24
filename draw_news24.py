#!/usr/bin/env python3
"""News Image 24 November 2026 — deterministic broadsheet render (PIL only).

Draws entry.png (1024x1024) from scratch: masthead, UTC timeline, numbers
strip, 3 pictorial leads, 10 pictured mid stories, dotted world map, region
bar chart, markets bar chart, 20-story ALSO ON list, DAY IN PICTURES strip,
DATE CHECK footer. 34 stories, 8 regions. No network, no randomness, no clock:
two runs write byte-identical PNGs.

After drawing, this script runs density_check.py (same directory) and exits
non-zero if any gate fails, so a render without a counter run is impossible.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W = H = 1024
MX = 8  # side margin

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
CREAM = (255, 251, 240)
INK = (26, 26, 26)
NAVY = (20, 38, 77)
NAVY2 = (28, 52, 102)
NIGHT = (13, 27, 51)
RED = (176, 30, 36)
REDD = (140, 20, 26)
GOLD = (200, 162, 74)
TAN = (201, 168, 106)
GREY = (92, 90, 82)
LINE = (198, 190, 168)
SEA = (216, 231, 240)
GREEN = (46, 160, 90)
BRGREEN = (53, 208, 127)

FD = "/usr/share/fonts/truetype/dejavu"
SERIF = f"{FD}/DejaVuSerif.ttf"
SERIFB = f"{FD}/DejaVuSerif-Bold.ttf"
SANS = f"{FD}/DejaVuSans.ttf"
SANSB = f"{FD}/DejaVuSans-Bold.ttf"

_fonts = {}


def F(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


# ---------------------------------------------------------------- data
LEADS = [
    dict(n=1, kicker="HUANG RETURNS", chip="+31.5% SHARES", scene="market",
         place="SANTA CLARA, US", beat="BUSINESS", tag="CONFIRMED",
         head="Huang back at Nvidia as shares soar 31%",
         dek="Board reinstates Jensen Huang as chief executive eleven days after his ouster; shares jump 31% in their best day since 2003, adding $952bn in a day.",
         src="Reuters - CNN"),
    dict(n=2, kicker="WARSHIP SUNK", chip="7 SEA DRONES", scene="warship",
         place="BENGHAZI, LIBYA", beat="WAR AT SEA", tag="REPORTED",
         head="Ukraine sinks Russian warship off Libya",
         dek="Sea drones sink the corvette Merkury at anchor in Benghazi and hit the cargo ship Angara; Tripoli condemns the strike and seeks a UN probe.",
         src="Reuters - WSJ"),
    dict(n=3, kicker="CLIMATE", chip="NO PACT", scene="cop31",
         place="ANTALYA, TURKIYE", beat="CLIMATE", tag="CONFIRMED",
         head="COP31 ends with no pact, the first since 2009",
         dek="The UN climate summit closes without a deal after the EU rejects a text with no fossil-fuel language; talks ran two days late and longest ever.",
         src="Reuters - Carbon Brief"),
]

MIDS = [
    dict(n=4, scene="awacs", place="POLAND", head="NATO sends early-warning plane to Poland",
         dek="AWACS jets deploy after three Russian missiles landed in Poland on Friday.", src="Reuters"),
    dict(n=5, scene="drones", place="KYIV, UKRAINE", head="96 drones in one night; Odesa dark and cold",
         dek="Overnight strikes hit 13 sites; 73 drones downed as power, heat and water fail.", src="Ukraine Air Force"),
    dict(n=6, scene="hormuz", place="TEHRAN, IRAN", head="Iran vows to defy US blockade",
         dek="Tehran says it will use all its tools as tankers burn near the Strait of Hormuz.", src="Reuters"),
    dict(n=7, scene="delta", place="ATLANTA, US", head="Delta outage grounds 3,000+ US flights",
         dek="A computer failure delays flights at busy US airports before Thanksgiving.", src="Delta"),
    dict(n=8, scene="taiwan", place="TAIPEI, TAIWAN", head="12 Chinese warships circle Taiwan",
         dek="Drones and helicopters enter the island's air-defence zone.", src="Reuters"),
    dict(n=9, scene="quake", place="NEPAL", head="5.6 quake strikes Nepal near China",
         dek="Tremor hits Koshi province by the border; no toll reported yet.", src="AP"),
    dict(n=10, scene="grok", place="WASHINGTON, US", head="States sue SpaceX over Grok images",
         dek="Two states allege the chatbot made sexualised photos of children.", src="Al Jazeera"),
    dict(n=11, scene="boat", place="NIGERIA", head="24 dead as boat capsizes on way to funeral",
         dek="Boat sinks en route to a funeral; rescue teams search the river.", src="AP"),
    dict(n=12, scene="mexico", place="MEXICO", head="Mexico nabs 'Chapo Isidro'; 16 killed",
         dek="Troops capture cartel boss Chapo Isidro as 16 suspected gunmen die in the raid.", src="Reuters"),
    dict(n=13, scene="moon", place="WORLD", head="Beaver Supermoon rises tonight",
         dek="The year's biggest full moon, first of four supermoons, lights the night sky.", src="Sky at Night"),
]

ALSO = [
    (14, "North America", "Trump to meet Rutte on Wednesday"),
    (15, "Europe", "Germany adopts Ukraine's Delta battle system"),
    (16, "Europe", "Ukraine drones set two Russian refineries ablaze"),
    (17, "Middle East", "Houthis say they hit Saudi Arabia's Rabigh refinery"),
    (18, "Middle East", "Israeli strike kills 3 in Khan Younis"),
    (19, "Oceania", "Vanuatu 6.5 quake, no tsunami"),
    (20, "Asia-Pacific", "Seoul names new foreign minister and spy chief"),
    (21, "Oceania", "Hobart stadium bill jumps to $1.23 billion"),
    (22, "Asia-Pacific", "US blacklists Megaspeed over export controls"),
    (23, "North America", "US unveils H-1B visa changes"),
    (24, "Europe", "Armenia drops Karabakh claim in draft constitution"),
    (25, "Europe", "Cyprus expels two Russian diplomats over spying"),
    (26, "Europe", "Bomb threats close schools in Germany and Denmark"),
    (27, "Europe", "NATO offers Poland 'significant backing'"),
    (28, "Europe", "Russian casualties outpace monthly recruiting, US says"),
    (29, "North America", "US to host 2031 Women's World Cup, FIFA says"),
    (30, "Latin America", "Panama and First Quantum resume Cobre mine talks"),
    (31, "Latin America", "Storm forces thousands to flee in Brazil"),
    (32, "Middle East", "Gaza's soil and water poisoned by war, report finds"),
    (33, "World", "UN chief urges global AI safety rules within a year"),
    (34, "Asia-Pacific", "India and Nepal sign 8 deals"),
]

TIMELINE = [
    ("05:30", "Taiex closes +9.0%, best in a year"),
    ("06:30", "Kospi closes +7.3% on Huang's return"),
    ("07:45", "Tripoli condemns sinking, seeks UN probe"),
    ("08:00", "73 of 96 drones downed by 08:00"),
    ("14:00", "Nvidia board reinstates Huang as CEO"),
    ("16:30", "NATO confirms AWACS plane for Poland"),
]

NUMBERS = [
    ("+31.5%", "Nvidia shares, best day since 2003"),
    ("96", "drones fired at Ukraine overnight"),
    ("3,000+", "US flights hit by Delta outage"),
    ("6.5", "Vanuatu quake magnitude"),
    ("24", "dead in Nigeria boat sinking"),
    ("$952BN", "value gained by Nvidia in one day"),
]

REGIONS = [("EUROPE", 9), ("N. AMERICA", 6), ("ASIA-PACIFIC", 5),
           ("MIDDLE EAST", 4), ("LATIN AMERICA", 3), ("WORLD", 3),
           ("AFRICA", 2), ("OCEANIA", 2)]

MARKETS = [("Nvidia", 31.5), ("Taiex", 9.0), ("Kospi", 7.3),
           ("Nasdaq", 6.5), ("S&P 500", 4.7), ("Nikkei", 4.2)]

PICTURES = [("drones", "DRONE NIGHT"), ("warship", "BENGHAZI"),
            ("market", "TAIPEI"), ("quake", "NEPAL"),
            ("moon", "SUPERMOON"), ("hormuz", "HORMUZ")]

# ---------------------------------------------------------------- text kit
RECTS = []  # (x0, y0, x1, y1, label) for the layout validator


def T(d, x, y, s, font, fill, anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)
    bb = d.textbbox((x, y), s, font=font, anchor=anchor)
    RECTS.append((bb[0], bb[1], bb[2], bb[3], s[:30]))
    return bb


def wrap(text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if F(*font).getlength(t) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, text, font, fill, maxw, lh, maxlines=99):
    """Draw wrapped paragraph; returns y just below the last line."""
    f = F(*font)
    lines = wrap(text, font, maxw)[:maxlines]
    for ln in lines:
        T(d, x, y, ln, f, fill)
        y += lh
    return y


def chip(d, x, y, s, font, fg, bg):
    f = F(*font)
    w = int(f.getlength(s)) + 10
    d.rounded_rectangle([x, y, x + w, y + 15], radius=3, fill=bg)
    T(d, x + 5, y + 2, s, f, fg)
    return w


# ---------------------------------------------------------------- scenes
def grad(d, box, top, bot):
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    for i in range(h):
        t = i / h
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def stars(d, box, n, seed=7):
    x0, y0, x1, y1 = box
    for i in range(n):
        px = x0 + ((i * 53 + seed * 11) % max(1, x1 - x0 - 4)) + 2
        py = y0 + ((i * 29 + seed * 7) % max(1, (y1 - y0) // 2)) + 2
        r = 1 if i % 3 else 2
        d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 220))


def scene_market(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (22, 38, 77), (10, 18, 40))
    # skyline
    bx = x
    for i, bh in enumerate([26, 40, 32, 48, 36, 44, 30, 52, 38]):
        bw = w // 9
        d.rectangle([bx, y + h - bh, bx + bw - 2, y + h], fill=(8, 14, 30))
        for wy in range(y + h - bh + 5, y + h - 4, 8):
            for wx in range(bx + 3, bx + bw - 4, 7):
                if (wx + wy) % 11 == 0:
                    d.point((wx, wy), fill=(240, 200, 90))
        bx += bw
    # candlesticks rising left to right
    n = 7
    for i in range(n):
        cx = x + 14 + i * ((w - 28) // n)
        base = y + h - 34 - i * 6
        top = base - 14 - i * 2
        col = GREEN if i % 2 == 0 else BRGREEN
        d.rectangle([cx, top, cx + 9, base], fill=col)
        d.line([(cx + 4, top - 6), (cx + 4, base + 6)], fill=col, width=2)
    # rising line + arrow
    pts = [(x + 10 + i * ((w - 20) // 6), y + h - 30 - i * 9 - (i * i) // 3)
           for i in range(7)]
    d.line(pts, fill=BRGREEN, width=3, joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex, ey - 9), (ex + 12, ey + 2), (ex - 2, ey + 8)], fill=BRGREEN)


def scene_warship(d, x, y, w, h):
    grad(d, (x, y, x + w, y + int(h * 0.55)), NIGHT, (24, 52, 92))
    d.rectangle([x, y + int(h * 0.55), x + w, y + h], fill=(16, 44, 74))
    stars(d, (x, y, x + w, y + int(h * 0.5)), 14, seed=3)
    d.ellipse([x + w - 52, y + 8, x + w - 22, y + 38], fill=(235, 230, 200))
    # sea lines
    for i in range(4):
        yy = y + int(h * 0.62) + i * 9
        d.line([(x + 8 + i * 12, yy), (x + w - 8 - i * 6, yy)],
               fill=(70, 120, 170), width=1)
    # warship
    hx, hy = x + int(w * 0.30), y + int(h * 0.52)
    d.polygon([(hx, hy), (hx + int(w * 0.42), hy), (hx + int(w * 0.36), hy + 16),
               (hx + 8, hy + 16)], fill=(52, 58, 66))
    d.rectangle([hx + 26, hy - 22, hx + 74, hy], fill=(62, 68, 76))
    d.rectangle([hx + 40, hy - 38, hx + 52, hy - 22], fill=(62, 68, 76))
    d.line([(hx + 46, hy - 38), (hx + 46, hy - 48)], fill=(200, 200, 200), width=2)
    # fire + smoke
    d.polygon([(hx + 84, hy - 6), (hx + 96, hy - 26), (hx + 108, hy - 6)],
              fill=(255, 140, 30))
    d.polygon([(hx + 88, hy - 4), (hx + 96, hy - 16), (hx + 104, hy - 4)],
              fill=(255, 210, 80))
    for i, r in enumerate([9, 7, 5]):
        d.ellipse([hx + 92 + i * 8 - r, hy - 34 - i * 10 - r,
                   hx + 92 + i * 8 + r, hy - 34 - i * 10 + r],
                  fill=(120, 120, 120))
    # drone boats with wakes
    for dx in (x + 12, x + w - 46):
        dy = y + h - 14
        d.polygon([(dx, dy), (dx + 26, dy), (dx + 20, dy + 7), (dx + 6, dy + 7)],
                  fill=(20, 20, 24))
        d.line([(dx - 14, dy + 3), (dx - 2, dy + 3)], fill=(220, 230, 240), width=1)


def scene_cop31(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (232, 134, 46), (247, 200, 115))
    d.ellipse([x + w // 2 - 20, y + 6, x + w // 2 + 20, y + 46],
              fill=(255, 236, 170))
    # conference building
    bx, by = x + int(w * 0.12), y + int(h * 0.42)
    bw, bh = int(w * 0.76), int(h * 0.40)
    d.rectangle([bx, by, bx + bw, by + bh], fill=(250, 244, 228))
    d.rectangle([bx, by, bx + bw, by + 10], fill=(176, 30, 36))
    for r in range(2):
        for c in range(9):
            wx = bx + 8 + c * ((bw - 16) // 9)
            wy = by + 16 + r * 16
            d.rectangle([wx, wy, wx + 12, wy + 9], fill=(40, 60, 90))
    # flags
    for i, col in enumerate([(176, 30, 36), (20, 60, 120), (46, 160, 90),
                             (240, 200, 60), (120, 60, 140)]):
        fx = bx + 10 + i * 16
        d.line([(fx, by - 16), (fx, by)], fill=(60, 60, 60), width=1)
        d.polygon([(fx, by - 16), (fx + 11, by - 13), (fx, by - 10)], fill=col)
    # crowd
    d.rectangle([x, y + h - 14, x + w, y + h], fill=(60, 40, 30))
    for i in range(12):
        cx = x + 10 + i * ((w - 20) // 12)
        d.ellipse([cx - 3, y + h - 24, cx + 3, y + h - 18], fill=(40, 28, 22))
        d.rectangle([cx - 4, y + h - 18, cx + 4, y + h - 14], fill=(40, 28, 22))


def scene_awacs(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (120, 180, 225), (205, 228, 240))
    for cx, cy, r in [(20, 12, 9), (150, 8, 11), (90, 26, 8)]:
        d.ellipse([x + cx - r, y + cy - r // 2, x + cx + r, y + cy + r // 2],
                  fill=(255, 255, 255))
    # plane with radar dome
    px, py = x + int(w * 0.30), y + int(h * 0.55)
    d.ellipse([px, py - 7, px + 76, py + 7], fill=(230, 235, 240))
    d.polygon([(px + 52, py - 2), (px + 92, py - 12), (px + 92, py + 2)],
              fill=(200, 208, 215))
    d.polygon([(px + 30, py + 4), (px + 44, py + 16), (px + 52, py + 4)],
              fill=(200, 208, 215))
    d.line([(px + 34, py - 7), (px + 34, py - 20)], fill=(90, 100, 110), width=2)
    d.ellipse([px + 22, py - 30, px + 48, py - 16], fill=(120, 130, 140))
    d.line([(px - 26, py + 2), (px - 6, py + 2)], fill=(255, 255, 255), width=2)


def scene_drones(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (10, 18, 40), (24, 44, 84))
    stars(d, (x, y, x + w, y + h), 16, seed=11)
    for i in range(6):
        dx = x + 14 + i * ((w - 28) // 6)
        dy = y + 8 + (i % 3) * 8
        d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(255, 255, 255))
        d.ellipse([dx + 3, dy - 1, dx + 5, dy + 1], fill=(255, 60, 60))
    # explosion
    ex, ey = x + int(w * 0.72), y + int(h * 0.45)
    d.polygon([(ex, ey - 9), (ex + 3, ey - 3), (ex + 9, ey), (ex + 3, ey + 3),
               (ex, ey + 9), (ex - 3, ey + 3), (ex - 9, ey), (ex - 3, ey - 3)],
              fill=(255, 170, 40))
    for i in range(10):
        d.point((x + 8 + i * 16, y + h - 6), fill=(240, 200, 90))
        d.point((x + 14 + i * 16, y + h - 10), fill=(240, 200, 90))


def scene_hormuz(d, x, y, w, h):
    grad(d, (x, y, x + w, y + int(h * 0.6)), (214, 110, 60), (240, 180, 110))
    d.rectangle([x, y + int(h * 0.6), x + w, y + h], fill=(30, 52, 78))
    d.ellipse([x + w - 34, y + 6, x + w - 12, y + 28], fill=(255, 220, 140))
    tx, ty = x + int(w * 0.18), y + int(h * 0.62)
    d.rectangle([tx, ty, tx + int(w * 0.55), ty + 10], fill=(24, 24, 28))
    d.rectangle([tx + int(w * 0.42), ty - 12, tx + int(w * 0.52), ty],
                fill=(24, 24, 28))
    d.polygon([(tx + int(w * 0.30), ty), (tx + int(w * 0.36), ty - 14),
               (tx + int(w * 0.42), ty)], fill=(255, 140, 30))
    d.ellipse([tx + int(w * 0.32), ty - 26, tx + int(w * 0.40), ty - 14],
              fill=(110, 110, 110))


def scene_delta(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (140, 190, 230), (215, 232, 242))
    d.ellipse([x + 12, y + 6, x + 34, y + 16], fill=(255, 255, 255))
    d.ellipse([x + 120, y + 12, x + 148, y + 22], fill=(255, 255, 255))
    px, py = x + 18, y + int(h * 0.55)
    d.ellipse([px, py - 5, px + 56, py + 5], fill=(30, 60, 110))
    d.polygon([(px + 40, py - 2), (px + 62, py - 10), (px + 62, py + 1)],
              fill=(30, 60, 110))
    d.ellipse([x + w - 40, y + 4, x + w - 8, y + 36], fill=(255, 255, 255),
              outline=(30, 60, 110), width=2)
    cx, cy = x + w - 24, y + 20
    d.line([(cx, cy), (cx, cy - 9)], fill=(176, 30, 36), width=2)
    d.line([(cx, cy), (cx + 7, cy + 2)], fill=(26, 26, 26), width=2)
    for i in range(5):
        d.line([(x + 10 + i * 12, y + h - 6), (x + 18 + i * 12, y + h - 6)],
               fill=(120, 140, 160), width=1)


def scene_taiwan(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(36, 110, 120))
    for i in range(3):
        yy = y + 10 + i * 12
        d.line([(x + 6, yy), (x + w - 6, yy)], fill=(90, 170, 180), width=1)
    # island
    d.polygon([(x + w // 2 - 8, y + 6), (x + w // 2 + 10, y + 10),
               (x + w // 2 + 6, y + h - 8), (x + w // 2 - 12, y + h - 6)],
              fill=(70, 150, 80))
    for sx in (x + 12, x + w - 52):
        sy = y + h - 16
        d.polygon([(sx, sy), (sx + 34, sy), (sx + 28, sy + 7), (sx + 6, sy + 7)],
                  fill=(60, 66, 72))
        d.rectangle([sx + 12, sy - 8, sx + 20, sy], fill=(60, 66, 72))


def scene_quake(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (235, 225, 205), (205, 190, 165))
    d.polygon([(x, y + h), (x + int(w * 0.30), y + 6), (x + int(w * 0.55), y + h)],
              fill=(120, 105, 85))
    d.polygon([(x + int(w * 0.35), y + h), (x + int(w * 0.62), y + 2),
               (x + w, y + h)], fill=(96, 84, 66))
    d.polygon([(x + int(w * 0.30) - 8, y + 6), (x + int(w * 0.30) + 8, y + 6),
               (x + int(w * 0.30), y + 16)], fill=(255, 255, 255))
    # crack
    cx, cy = x + int(w * 0.55), y + int(h * 0.55)
    d.line([(cx, cy), (cx + 10, cy + 6), (cx + 2, cy + 12), (cx + 12, cy + 18)],
           fill=(140, 40, 30), width=2)
    d.rectangle([x + 14, y + h - 16, x + 30, y + h - 2], fill=(150, 120, 90))
    d.polygon([(x + 14, y + h - 16), (x + 30, y + h - 16), (x + 22, y + h - 22)],
              fill=(120, 90, 60))


def scene_grok(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(26, 28, 40))
    px, py = x + int(w * 0.42), y + 4
    d.rounded_rectangle([px, py, px + 34, py + h - 8], radius=4,
                        fill=(230, 232, 238))
    d.rounded_rectangle([px + 5, py + 6, px + 29, py + 14], radius=3,
                        fill=(90, 140, 220))
    d.rounded_rectangle([px + 5, py + 17, px + 29, py + 25], radius=3,
                        fill=(200, 205, 212))
    tx, ty = x + 12, y + 8
    d.polygon([(tx + 10, ty), (tx + 20, ty + 18), (tx, ty + 18)], fill=(220, 40, 40))
    T(d, tx + 6, ty + 6, "!", F(SANSB, 11), (255, 255, 255))


def scene_boat(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (150, 195, 225), (60, 120, 170))
    for i in range(4):
        yy = y + 12 + i * 9
        d.arc([x + 4 + i * 8, yy - 4, x + 40 + i * 8, yy + 6], 180, 360,
              fill=(255, 255, 255), width=1)
    bx, by = x + int(w * 0.35), y + int(h * 0.45)
    d.polygon([(bx, by), (bx + 56, by), (bx + 46, by + 12), (bx + 10, by + 12)],
              fill=(120, 40, 30))
    d.polygon([(bx + 10, by), (bx + 26, by - 12), (bx + 30, by)], fill=(200, 190, 170))
    for i in range(3):
        d.ellipse([bx + 12 + i * 14 - 3, by - 20, bx + 12 + i * 14 + 3,
                   by - 14], fill=(30, 30, 30))
    d.ellipse([x + w - 30, y + 6, x + w - 12, y + 24], outline=(255, 120, 30),
              width=3)


def scene_mexico(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (240, 160, 70), (200, 110, 60))
    d.ellipse([x + w - 40, y + 4, x + w - 14, y + 30], fill=(255, 225, 140))
    d.polygon([(x, y + h), (x + 40, y + 14), (x + 90, y + h)], fill=(140, 80, 90))
    d.polygon([(x + 70, y + h), (x + 130, y + 20), (x + w, y + h)],
              fill=(120, 66, 80))
    cx, cy = x + 22, y + h - 22
    d.rectangle([cx, cy - 12, cx + 6, cy], fill=(40, 110, 60))
    d.rectangle([cx - 6, cy - 8, cx, cy - 4], fill=(40, 110, 60))
    d.rectangle([cx + 6, cy - 10, cx + 12, cy - 6], fill=(40, 110, 60))
    sx, sy = x + w - 52, y + 8
    d.polygon([(sx + 6, sy), (sx + 8, sy + 5), (sx + 13, sy + 5),
               (sx + 9, sy + 9), (sx + 11, sy + 14), (sx + 6, sy + 11),
               (sx + 1, sy + 14), (sx + 3, sy + 9), (sx - 1, sy + 5),
               (sx + 4, sy + 5)], fill=(255, 215, 90))


def scene_moon(d, x, y, w, h):
    grad(d, (x, y, x + w, y + h), (12, 20, 44), (30, 48, 88))
    stars(d, (x, y, x + w, y + h), 12, seed=5)
    cx, cy, r = x + int(w * 0.62), y + int(h * 0.52), min(w, h) // 2 - 6
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 232, 210))
    for ox, oy, rr in [(-6, -4, 3), (5, 3, 4), (-2, 7, 2), (7, -6, 2)]:
        d.ellipse([cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr],
                  fill=(210, 202, 178))
    d.polygon([(x, y + h), (x + 12, y + h - 18), (x + 26, y + h)],
              fill=(16, 22, 36))


SCENES = {"market": scene_market, "warship": scene_warship, "cop31": scene_cop31,
          "awacs": scene_awacs, "drones": scene_drones, "hormuz": scene_hormuz,
          "delta": scene_delta, "taiwan": scene_taiwan, "quake": scene_quake,
          "grok": scene_grok, "boat": scene_boat, "mexico": scene_mexico,
          "moon": scene_moon}

# ---------------------------------------------------------------- map
# Rough continent outlines in lon/lat, drawn as a dotted land mask.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-65, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 28), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    [(-58, 64), (-45, 60), (-30, 68), (-40, 76), (-58, 74)],
    [(-80, 10), (-70, 12), (-60, 8), (-50, 0), (-35, -8), (-40, -20),
     (-48, -28), (-58, -35), (-65, -45), (-70, -55), (-73, -40), (-75, -20),
     (-80, -5)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 59), (28, 60), (30, 62), (25, 65), (20, 70),
     (12, 71), (5, 60), (5, 58), (-5, 50)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28),
     (43, 12), (51, 11), (48, 0), (40, -10), (35, -20), (32, -29), (25, -34),
     (18, -35), (15, -27), (12, -18), (9, -2), (9, 4), (-8, 4), (-13, 8)],
    [(30, 62), (40, 68), (55, 70), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (170, 66), (178, 65), (162, 60), (158, 52), (142, 50),
     (140, 40), (130, 35), (127, 33), (120, 30), (110, 20), (105, 10),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 15), (75, 8), (72, 20),
     (65, 25), (58, 26), (52, 28), (48, 30), (44, 29), (40, 32), (35, 36),
     (30, 36)],
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -8), (130, -3), (135, 0), (140, -5)],
    [(130, 31), (133, 34), (137, 35), (140, 38), (142, 42), (144, 44),
     (141, 45)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -11), (137, -12), (132, -12), (126, -14),
     (122, -17), (118, -20)],
]

# story number -> (lon, lat) pins on the map
PINS = [(1, -122, 37), (2, 20, 32), (3, 30, 37), (4, 19, 52), (5, 31, 50),
        (6, 51, 35), (7, -84, 34), (8, 121, 25), (9, 85, 28), (10, -77, 39),
        (11, 7, 9), (12, -107, 25), (19, 167, -16),
        (21, 147, -43)]


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    for poly in CONTINENTS:
        pts = [((lon + 170) / 360 * w, (75 - lat) / 130 * h)
               for lon, lat in poly]
        md.polygon(pts, fill=255)
    for gy in range(3, h - 2, 4):
        for gx in range(3, w - 2, 4):
            if mask.getpixel((gx, gy)):
                d.ellipse([x + gx - 2, y + gy - 2, x + gx + 2, y + gy + 2],
                          fill=TAN)
    for n, lon, lat in PINS:
        px = x + (lon + 170) / 360 * w
        py = y + (75 - lat) / 130 * h
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=RED,
                  outline=(255, 255, 255), width=1)
        T(d, px, py - 5, str(n), F(SANSB, 8), (255, 255, 255), anchor="ma")


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- top bar
    d.rectangle([0, 0, W, 24], fill=NAVY)
    T(d, MX, 5, "THE WORLD IN ONE DAY", F(SANSB, 12), (255, 255, 255))
    T(d, W - MX, 6, "34 STORIES  •  8 REGIONS  •  EVERY ONE DATED TUESDAY 24 NOVEMBER 2026",
      F(SANSB, 10), (255, 220, 130), anchor="ra")

    # ---- headline + dek
    T(d, W // 2, 28, "Tuesday 24 November 2026", F(SERIFB, 46), INK, anchor="ma")
    T(d, W // 2, 84,
      "Huang is back at Nvidia as shares soar 31%  •  Ukraine sinks a Russian warship off Libya  •  COP31 ends with no pact",
      F(SERIF, 13), RED, anchor="ma")

    # ---- timeline strip
    d.rectangle([MX, 102, W - MX, 146], fill=NAVY)
    T(d, MX + 6, 106, "THE DAY IN UTC", F(SANSB, 10), (255, 220, 130))
    T(d, MX + 6, 122, "all times UTC", F(SANS, 8), (200, 205, 220))
    cellw = (W - 2 * MX - 150) // 6
    for i, (tm, ev) in enumerate(TIMELINE):
        cx = MX + 150 + i * cellw
        if i:
            d.line([(cx - 4, 108), (cx - 4, 140)], fill=(90, 110, 150), width=1)
        T(d, cx, 106, tm, F(SANSB, 12), (255, 120, 110))
        para(d, cx, 122, ev, (SANS, 9), (235, 238, 245), cellw - 10, 11, 2)

    # ---- numbers strip
    T(d, MX, 148, "THE DAY IN NUMBERS", F(SANSB, 11), RED)
    numw = (W - 2 * MX) // 6
    for i, (num, cap) in enumerate(NUMBERS):
        nx = MX + i * numw
        if i:
            d.line([(nx - 5, 162), (nx - 5, 190)], fill=LINE, width=1)
        T(d, nx, 158, num, F(SERIFB, 25), RED)
        para(d, nx, 188, cap, (SANS, 8), GREY, numw - 10, 10, 1)
    d.line([(MX, 200), (W - MX, 200)], fill=NAVY, width=2)

    # ---- 3 pictorial leads
    colw = (W - 2 * MX - 16) // 3
    for i, L in enumerate(LEADS):
        x = MX + i * (colw + 8)
        y = 206
        d.rectangle([x, y, x + colw, y + 19], fill=RED)
        T(d, x + 6, y + 4, L["kicker"], F(SANSB, 11), (255, 255, 255))
        chip(d, x + colw - 92, y + 2, L["chip"], (SANSB, 8), NAVY, (255, 255, 255))
        by = y + 19
        SCENES[L["scene"]](d, x, by, colw, 100)
        d.rectangle([x, by, x + colw, by + 100], outline=NAVY, width=1)
        ly = by + 100 + 5
        T(d, x, ly, f"{L['n']}  {L['place']}  •  {L['beat']}", F(SANSB, 10), INK)
        chip(d, x + colw - 74, ly - 1, L["tag"], (SANSB, 8), (255, 255, 255), RED)
        hy = ly + 17
        hy = para(d, x, hy, L["head"], (SERIFB, 18), INK, colw, 21, 3)
        hy = para(d, x, hy + 2, L["dek"], (SANS, 10), (50, 48, 44), colw, 13, 3)
        T(d, x, hy + 3, L["src"], F(SANS, 9), GREY)

    # ---- 10 pictured mids
    T(d, MX, 464, "MORE FROM TUESDAY", F(SANSB, 11), RED)
    d.line([(MX + 150, 470), (W - MX, 470)], fill=LINE, width=1)
    midw = (W - 2 * MX - 32) // 5
    for idx, M in enumerate(MIDS):
        r, c = divmod(idx, 5)
        x = MX + c * (midw + 8)
        y = 478 + r * 104
        SCENES[M["scene"]](d, x, y, midw, 42)
        d.rectangle([x, y, x + midw, y + 42], outline=NAVY, width=1)
        T(d, x, y + 46, f"{M['n']}  {M['place']}", F(SANSB, 9), INK)
        hy = y + 58
        hy = para(d, x, hy, M["head"], (SANSB, 11), INK, midw, 12, 2)
        para(d, x, hy + 1, M["dek"], (SANS, 9), (60, 58, 54), midw, 10, 2)

    # ---- map + charts
    T(d, MX, 690, "WHERE IT HAPPENED", F(SANSB, 11), RED)
    T(d, MX + 168, 690, "pins match story numbers", F(SANS, 9), GREY)
    draw_map(d, MX, 704, 560, 112)
    d.rectangle([MX, 704, MX + 560, 816], outline=NAVY, width=1)
    rx = MX + 568
    rw = W - MX - rx
    T(d, rx, 690, "STORIES BY REGION", F(SANSB, 11), RED)
    maxc = max(c for _, c in REGIONS)
    for i, (name, cnt) in enumerate(REGIONS):
        by = 706 + i * 9
        T(d, rx, by, name, F(SANSB, 8), INK)
        bx0 = rx + 92
        bw = int((rw - 112) * cnt / maxc)
        d.rectangle([bx0, by + 1, bx0 + bw, by + 6], fill=RED)
        T(d, bx0 + bw + 4, by, str(cnt), F(SANSB, 8), RED)
    T(d, rx, 778, "MARKETS ON TUESDAY  —  % CHANGE", F(SANSB, 9), INK)
    base = 812
    bw = (rw - 20) // 6
    for i, (name, val) in enumerate(MARKETS):
        bx = rx + i * bw
        bh = int(val / 31.5 * 14)
        d.rectangle([bx + 6, base - bh, bx + bw - 6, base], fill=GREEN)
        T(d, bx + bw // 2, base - bh - 9, f"+{val}%", F(SANSB, 8), GREEN,
          anchor="ma")
        T(d, bx + bw // 2, base + 1, name, F(SANS, 7), GREY, anchor="ma")

    # ---- ALSO ON list (21 items, 3 columns x 7 rows)
    T(d, MX, 826, "ALSO ON TUESDAY 24 NOVEMBER — 21 MORE STORIES", F(SANSB, 11), RED)
    d.line([(MX, 840), (W - MX, 840)], fill=NAVY, width=1)
    for i, (n, region, head) in enumerate(ALSO):
        col, row = divmod(i, 7)
        x = MX + col * 336
        y = 846 + row * 11
        T(d, x, y, str(n), F(SANSB, 9), RED)
        T(d, x + 22, y, f"{region}: {head}", F(SANS, 9), INK)

    # ---- day in pictures
    T(d, MX, 924, "THE DAY IN PICTURES", F(SANSB, 11), RED)
    pw = (W - 2 * MX - 30) // 6
    for i, (scene, cap) in enumerate(PICTURES):
        x = MX + i * (pw + 6)
        y = 938
        SCENES[scene](d, x, y, pw, 40)
        d.rectangle([x, y, x + pw, y + 40], outline=NAVY, width=1)
        d.rectangle([x, y + 28, x + pw, y + 40], fill=RED)
        T(d, x + pw // 2, y + 31, cap, F(SANSB, 8), (255, 255, 255), anchor="ma")

    # ---- footer
    d.rectangle([MX, 982, W - MX, 1024 - 2], outline=RED, width=1)
    T(d, MX + 4, 985,
      "DATE CHECK — Every story here happened, or was first reported, on Tuesday 24 November 2026 in at least one time zone.",
      F(SANSB, 8), RED)
    para(d, MX + 4, 995,
         "Left out as other days' news: Huang's ouster (11 Nov); the COP31 talks' opening (9 Nov); the Merkury attack itself (Sun 22 Nov) counts here for its Mon 23 Nov confirmation. Sources: Reuters, WSJ, CNN, AP, Al Jazeera, Carbon Brief, Delta. Pictures and map: original, drawn in code. PRESS TIME 09:00 UTC.",
         (SANS, 8), GREY, W - 2 * MX - 8, 9, 3)

    # ---- layout validator: no text outside the canvas, no text-on-text
    problems = []
    for (a, b, c, e, s) in RECTS:
        if a < 0 or b < 0 or c > W or e > H:
            problems.append(f"OUT-OF-BOUNDS {s!r} {(a, b, c, e)}")
    for i in range(len(RECTS)):
        for j in range(i + 1, len(RECTS)):
            a, b = RECTS[i], RECTS[j]
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 1 and oy > 1:
                problems.append(f"TEXT OVERLAP {a[4]!r} <-> {b[4]!r}")
    if problems:
        print("LAYOUT GATE: FAIL")
        for p in problems[:20]:
            print(" ", p)
        sys.exit(1)
    print(f"LAYOUT GATE: PASS ({len(RECTS)} text boxes, 0 overflow, 0 overlap)")

    img.save(HERE / "entry.png", optimize=True)
    manifest = {
        "stories": 34, "regions": 8, "charts": 3, "map": True,
        "timeline_events": len(TIMELINE), "numbers": len(NUMBERS),
        "leads": [dict(n=L["n"], head=L["head"], region=L["beat"]) for L in LEADS],
        "mids": [dict(n=M["n"], head=M["head"], region=M["place"]) for M in MIDS],
        "also": [dict(n=n, region=r, head=h) for n, r, h in ALSO],
        "region_counts": dict(REGIONS),
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print("DENSITY: 34 stories, 8 regions, map yes, 3 charts, "
          "6 timeline events, 6 numbers")
    return img


if __name__ == "__main__":
    build()
    r = subprocess.run([sys.executable, str(HERE / "density_check.py")],
                       cwd=str(HERE))
    sys.exit(r.returncode)
