#!/usr/bin/env python3
"""
Zombie 5 (big brute): 8 dance frames + 7 body parts.

Run:   python3 make_zombie5.py [output_dir]
Needs: pip install pillow numpy
Output (default ./zombie5/):
    zombie5_dance0.png ... zombie5_dance7.png     160x200, transparent
    zombie5_head / torso / armL / armR / legL / legR / extra .png   (<= 64x64)
    zombie5_preview.png                            contact sheet (not part of the set)

Same method as make_zombie1.py: everything is drawn on a 40x50 grid of
"logical pixels" using palette indices, then scaled 4x with nearest-neighbour
(-> 160x200). A 1-logical-pixel outline is added automatically.

SIZE: the brute is drawn bigger than the others on the same canvas: the body
is 16 px wide (the others are 12) and the sprite runs from the top of the
canvas to the ground at the very bottom (rows 1..49, 196 px tall; the others
use 168 px). A true 1.3x in height cannot fit in 200 px because zombie 1 is
already 168 px tall, so the extra size comes mostly from bulk: head 14 wide
(12), torso 16 wide (12), legs 7 wide (5), fists 5x7 (4x6).

PARTS: at the frames' pixel scale (4) the brute's torso would be 72x84 px, over
the 64x64 limit, so the part sprites are exported at PART_SCALE = 3 (pixels 3x3
instead of 4x4). Set PART_SCALE = 4 if you would rather have pixel-identical
parts and accept sizes above 64 px.

Where to change things
  * PAL                          the 15-colour palette (index -> RGB)
  * head() torso() leg() arm() reach_arm() stitched_hand()   the part drawings
  * the DANCE table              one row per frame (body shift, head tilt,
                                 torso bob, which foot is stomped up, arm poses)
  * POSES                        pose name -> arm drawing
  * S / PART_SCALE               pixel scale for frames / for part sprites

Screen-left (viewer's left) = "L", screen-right = "R", as in zombie 1.
"""
import os
import sys

import numpy as np
from PIL import Image

S = 4                       # scale factor for the dance frames
PART_SCALE = 4              # scale factor for the body-part sprites (see above)
W, H = 40, 50               # logical canvas  (x4 = 160 x 200)
CX = 20                     # horizontal centre of the character
GROUND = 49                 # logical row just below the feet (outline row, last row of canvas)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "zombie5")

# 15 colours + transparent (index 0). Edit these to recolour the zombie.
PAL = {
    1: (28, 24, 34),      # outline
    2: (84, 76, 104),     # skin dark  (grey lilac)
    3: (124, 116, 144),   # skin mid
    4: (166, 158, 184),   # skin light
    5: (122, 160, 178),   # gown shade
    6: (172, 204, 216),   # gown
    7: (214, 232, 238),   # gown light
    8: (36, 28, 40),      # stitch thread
    9: (178, 84, 96),     # scar flesh
    10: (236, 232, 204),  # eye white
    11: (58, 20, 32),     # pupil / mouth
    12: (240, 234, 206),  # teeth / tusks
    13: (214, 190, 120),  # toenails
    14: (92, 126, 168),   # gown print / trim
    15: (230, 150, 60),   # hospital wristband
}


# ------------------------------------------------------------------ canvas
class C:
    """Tiny indexed-colour pixel canvas (0 = transparent)."""

    def __init__(s, w, h):
        s.w, s.h = w, h
        s.g = [[0] * w for _ in range(h)]

    def set(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.g[y][x] = c

    def rect(s, x, y, w, h, c):
        for j in range(y, y + h):
            for i in range(x, x + w):
                s.set(i, j, c)

    def paste(s, o, ox, oy):
        for j in range(o.h):
            for i in range(o.w):
                if o.g[j][i]:
                    s.set(ox + i, oy + j, o.g[j][i])

    def flip(s):
        o = C(s.w, s.h)
        o.g = [row[::-1] for row in s.g]
        return o

    def outline(s):
        add = []
        for y in range(s.h):
            for x in range(s.w):
                if s.g[y][x] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < s.w and 0 <= ny < s.h and s.g[ny][nx]:
                            add.append((x, y))
                            break
        for x, y in add:
            s.g[y][x] = 1

    def crop(s, margin=0):
        ys = [y for y in range(s.h) if any(s.g[y])]
        xs = [x for x in range(s.w) if any(s.g[y][x] for y in range(s.h))]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        o = C(x1 - x0 + 1 + 2 * margin, y1 - y0 + 1 + 2 * margin)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                o.g[y - y0 + margin][x - x0 + margin] = s.g[y][x]
        return o

    def image(s, scale=S):
        a = np.zeros((s.h, s.w, 4), dtype=np.uint8)
        for y in range(s.h):
            for x in range(s.w):
                v = s.g[y][x]
                if v:
                    a[y, x] = (*PAL[v], 255)
        return Image.fromarray(a, "RGBA").resize((s.w * scale, s.h * scale), Image.NEAREST)


# ------------------------------------------------------------- body parts
def head():
    """Bald, 14 px wide, heavy brow, two tusks, stitched crown and cheek."""
    c = C(14, 13)
    rows = {0: (4, 9), 1: (2, 11), 2: (1, 12), 3: (0, 13), 4: (0, 13), 5: (0, 13),
            6: (0, 13), 7: (0, 13), 8: (0, 13), 9: (1, 12), 10: (1, 12),
            11: (3, 10), 12: (4, 9)}
    for y, (a, b) in rows.items():
        for x in range(a, b + 1):
            c.set(x, y, 3)
    for y in range(3, 11):
        c.set(0, y, 4)
        c.set(13, y, 2)
    c.rect(3, 1, 3, 1, 4)              # bald-head shine
    c.set(2, 2, 4)
    c.rect(4, 12, 6, 1, 2)
    c.rect(2, 11, 2, 1, 2)
    c.rect(10, 11, 1, 1, 2)
    # stitched scar across the crown
    c.rect(4, 2, 6, 1, 9)
    for x in (5, 7, 9):
        c.set(x, 1, 8)
        c.set(x, 3, 8)
    # heavy brow, small angry eyes
    c.rect(2, 4, 4, 1, 11)
    c.rect(8, 4, 4, 1, 11)
    c.rect(3, 5, 3, 2, 10)
    c.rect(8, 5, 3, 2, 10)
    c.set(4, 6, 11)
    c.set(9, 6, 11)
    c.rect(2, 7, 4, 1, 2)
    c.rect(8, 7, 4, 1, 2)
    # wide nose
    c.rect(6, 6, 2, 2, 2)
    # grimace with two upturned tusks
    c.rect(3, 9, 8, 1, 11)
    c.rect(4, 10, 6, 1, 11)
    c.set(3, 8, 12)
    c.set(10, 8, 12)
    c.set(5, 9, 12)
    c.set(8, 9, 12)
    # stitched cheek scar
    c.rect(11, 5, 1, 5, 9)
    c.set(10, 6, 8)
    c.set(12, 6, 8)
    c.set(10, 8, 8)
    c.set(12, 8, 8)
    return c


def torso():
    """Hospital gown: V neck, blue print, ragged hem, torn open at the belly
    to show a stitched scar. 16 wide."""
    c = C(16, 19)
    c.rect(0, 0, 16, 17, 6)
    c.rect(0, 0, 3, 17, 7)
    c.rect(12, 0, 4, 17, 5)
    for y, (a, b) in {0: (4, 11), 1: (5, 10), 2: (6, 9), 3: (7, 8)}.items():
        for x in range(a, b + 1):
            c.set(x, y, 3)
        c.set(a - 1, y, 14)            # blue neck trim
        c.set(b + 1, y, 14)
    for x, y in ((2, 5), (6, 6), (13, 4), (4, 11), (9, 10), (12, 12), (7, 14),
                 (1, 13), (14, 8), (10, 15), (3, 16)):
        c.set(x, y, 14)                # gown print
    # torn belly with a stitched scar
    c.rect(5, 7, 6, 6, 3)
    c.set(5, 7, 6)
    c.set(10, 12, 6)
    c.rect(10, 7, 1, 6, 2)
    c.rect(7, 7, 1, 6, 9)
    for y in (8, 10, 12):
        c.set(6, y, 8)
        c.set(8, y, 8)
    # ragged hem
    for x in (0, 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 15):
        c.set(x, 17, 7 if x < 3 else (5 if x >= 12 else 6))
    for x in (0, 2, 5, 8, 11, 14):
        c.set(x, 18, 7 if x < 3 else (5 if x >= 12 else 6))
    return c


def leg(side, short=0):
    """Thick bare leg and big bare foot with toenails. short = rows removed
    for a knee bend (total height is 19 - short)."""
    n = 16 - short                     # leg rows
    c = C(8, 19 - short)
    b = 1 if side == "L" else 0
    c.rect(b, 0, 7, n, 3)
    c.rect(b, 0, 2, n, 4)
    c.rect(b + 5, 0, 2, n, 2)
    if side == "R":                    # stitched scar across the knee
        c.rect(b + 1, 6, 5, 1, 9)
        for x in (b + 2, b + 4):
            c.set(x, 5, 8)
            c.set(x, 7, 8)
    c.rect(0, n, 8, 2, 3)              # foot
    c.rect(0, n, 8, 1, 4)
    c.rect(6, n, 2, 2, 2)
    for x in range(8):                 # toes
        c.set(x, n + 2, 13 if x % 2 == 0 else 2)
    return c


def stitched_hand():
    c = C(8, 9)
    for x in (0, 2, 4, 6):             # fingers
        c.rect(x, 0, 1, 2, 3)
    c.rect(0, 2, 7, 4, 3)
    c.rect(0, 2, 1, 4, 4)
    c.rect(6, 2, 1, 4, 2)
    c.rect(0, 5, 7, 1, 2)
    c.rect(7, 3, 1, 2, 3)              # thumb
    c.rect(1, 6, 5, 2, 3)              # wrist with stitches
    c.rect(1, 6, 5, 1, 9)
    c.set(2, 7, 8)
    c.set(4, 7, 8)
    c.rect(1, 7, 5, 1, 15)             # hospital wristband
    c.set(2, 7, 8)
    c.set(2, 8, 2)
    c.set(4, 8, 2)
    return c


def arm(hy=0):
    """Screen-left arm held out sideways; returns (canvas, ax, sy).
    ax = local x of the sleeve edge that touches the torso, sy = local row of
    the sleeve top. hy moves the hand up (-) or down (+) from level
    (-6 raised, -3 half, 0 level, +4 lowered). Gown sleeve, thick arm, big fist
    with a hospital wristband."""
    sy = 14
    c = C(11, 25)
    ht = sy - 1 + hy                   # hand top row
    y0, y1 = min(sy + 1, ht + 2), max(sy + 3, ht + 5)
    c.rect(5, y0, 3, y1 - y0 + 1, 3)   # forearm
    c.rect(5, y0, 3, 1, 4)
    c.rect(5, y1, 3, 1, 2)
    c.rect(1, ht, 5, 7, 3)             # big fist
    c.rect(1, ht, 1, 7, 4)
    c.rect(5, ht, 1, 7, 2)
    c.rect(1, ht + 6, 5, 1, 2)
    for k in (1, 3, 5):                # knuckles
        c.set(0, ht + k, 3)
    c.rect(2, ht - 1, 2, 1, 3)         # thumb
    c.rect(6, ht + 1, 1, 5, 15)        # wristband
    c.rect(7, sy, 4, 5, 6)             # short gown sleeve
    c.rect(7, sy, 4, 1, 7)
    c.rect(10, sy, 1, 5, 5)
    c.rect(7, sy + 1, 1, 3, 14)
    c.set(7, sy + 4, 0)
    return c, 10, sy


def reach_arm():
    """Zombie reach: the arm widens toward the hand (sleeve 4 px, forearm
    4 px, hand 5x9 px) so it reads as stretching toward the viewer."""
    c = C(11, 14)
    c.rect(4, 4, 4, 6, 3)              # forearm
    c.rect(4, 4, 4, 1, 4)
    c.rect(4, 9, 4, 1, 2)
    c.rect(0, 1, 5, 8, 3)              # big hand
    c.rect(0, 1, 1, 8, 4)
    c.rect(4, 1, 1, 8, 2)
    c.rect(0, 8, 5, 1, 2)
    for x in (0, 2, 4):                # fingers up
        c.set(x, 0, 3)
    c.set(5, 5, 3)                     # thumb
    c.rect(5, 3, 1, 5, 15)             # wristband
    c.rect(7, 8, 4, 5, 6)              # sleeve
    c.rect(7, 8, 4, 1, 7)
    c.rect(10, 8, 1, 5, 5)
    c.rect(7, 9, 1, 3, 14)
    return c, 10, 8


# ------------------------------------------------------------------ dance
# One row per frame.
#   dx      body shift left/right (logical px; the brute only has room for +-1)
#   tilt    head tilt: how far the top of the head leans (px)
#   bob     torso/head/arms drop by this many px; legs get shorter by the same
#           amount, so the feet stay on the ground. bob 3 = heavy knee bend
#   liftL/R how many px that foot is stomped up (weight goes onto the other)
#   armL/R  pose names, see POSES
DANCE = [
    dict(dx=1,  tilt=-2, bob=0, liftL=2, liftR=0, armL="up",    armR="down"),
    dict(dx=1,  tilt=-3, bob=0, liftL=3, liftR=0, armL="reach", armR="reach"),   # foot at the top
    dict(dx=0,  tilt=-1, bob=3, liftL=0, liftR=0, armL="down",  armR="up"),      # STOMP, knees bent
    dict(dx=0,  tilt=1,  bob=1, liftL=0, liftR=1, armL="out",   armR="out"),
    dict(dx=-1, tilt=2,  bob=0, liftL=0, liftR=2, armL="down",  armR="up"),
    dict(dx=-1, tilt=3,  bob=0, liftL=0, liftR=3, armL="reach", armR="reach"),   # foot at the top
    dict(dx=0,  tilt=1,  bob=3, liftL=0, liftR=0, armL="up",    armR="down"),    # STOMP, knees bent
    dict(dx=0,  tilt=-1, bob=1, liftL=1, liftR=0, armL="out",   armR="out"),
]
POSES = {
    "out": lambda: arm(0),
    "up": lambda: arm(-6),
    "mid": lambda: arm(-3),
    "down": lambda: arm(4),
    "reach": lambda: reach_arm(),
}


def sheared_head(tilt):
    """Head leaning by `tilt` px at the top, pivoting around the chin."""
    h = head()
    o = C(20, 13)
    for r in range(13):
        sh = round(tilt * (12 - r) / 12)
        for i in range(h.w):
            if h.g[r][i]:
                o.set(3 + sh + i, r, h.g[r][i])
    return o


def put_arm(c, drawn, side, dx, bob):
    a, ax, sy = drawn
    oy = 15 + bob - sy                 # shoulder row is 15
    if side == "L":
        c.paste(a, CX - 8 + dx - ax, oy)
    else:
        a = a.flip()
        c.paste(a, CX + 7 + dx - (a.w - 1 - ax), oy)


def frame(f):
    d = DANCE[f]
    dx, bob = d["dx"], d["bob"]
    c = C(W, H)

    # legs: shorter when the knees bend; a stomping foot is lifted
    for side, lift, x in (("L", d["liftL"], 11 + dx), ("R", d["liftR"], 21 + dx)):
        lg = leg(side, bob)
        c.paste(lg, x, GROUND - lg.h - lift)

    # filler under the gown, then torso
    c.rect(CX - 8 + dx, 30 + bob, 16, 3, 3)
    c.rect(CX + 4 + dx, 30 + bob, 4, 3, 2)
    c.paste(torso(), CX - 8 + dx, 13 + bob)

    # arms
    put_arm(c, POSES[d["armL"]](), "L", dx, bob)
    put_arm(c, POSES[d["armR"]](), "R", dx, bob)

    # head (tilted); it sits on the shoulders, no visible neck
    c.paste(sheared_head(d["tilt"]), CX - 7 + dx - 3, 2 + bob)

    c.outline()
    return c


# ------------------------------------------------------------------- main
def build_parts():
    """Body-part sprites, drawn at the same logical size as the frames."""
    return {
        "head": head(),
        "torso": torso(),
        "armL": arm(0)[0],
        "armR": arm(0)[0].flip(),
        "legL": leg("L"),
        "legR": leg("R"),
        "extra": stitched_hand(),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in range(8):
        frame(f).image().save(os.path.join(OUT, f"zombie5_dance{f}.png"))

    parts = build_parts()
    for name, p in parts.items():
        big = C(p.w + 4, p.h + 4)
        big.paste(p, 2, 2)
        big.outline()
        big.crop(0).image(PART_SCALE).save(os.path.join(OUT, f"zombie5_{name}.png"))

    # contact sheet (preview only)
    sheet = Image.new("RGBA", (160 * 4 + 50, 200 * 2 + 30 + 80 + 30), (88, 92, 104, 255))
    for i in range(8):
        im = Image.open(os.path.join(OUT, f"zombie5_dance{i}.png"))
        sheet.alpha_composite(im, (10 + (i % 4) * 170, 10 + (i // 4) * 210))
    x = 10
    for name in parts:
        im = Image.open(os.path.join(OUT, f"zombie5_{name}.png"))
        sheet.alpha_composite(im, (x, 440))
        x += im.width + 12
    sheet.save(os.path.join(OUT, "zombie5_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
