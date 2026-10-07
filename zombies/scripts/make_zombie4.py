#!/usr/bin/env python3
"""
Zombie 4 (zombie rocker): 8 dance frames + 7 body parts.

Run:   python3 make_zombie4.py [output_dir]
Needs: pip install pillow numpy
Output (default ./zombie4/):
    zombie4_dance0.png ... zombie4_dance7.png     160x200, transparent
    zombie4_head / torso / armL / armR / legL / legR / extra .png   (<= 64x64)
    zombie4_preview.png                            contact sheet (not part of the set)

Same method as make_zombie1.py: everything is drawn on a 40x50 grid of
"logical pixels" using palette indices, then scaled 4x with nearest-neighbour
(-> 160x200). A 1-logical-pixel outline is added automatically.

Where to change things
  * PAL                          the 16-colour palette (index -> RGB)
  * head() torso() leg() arm() strum_arm() popped_eye()   the part drawings
  * the DANCE table              one row per frame (body shift, head tilt,
                                 torso bob, head bang, arm poses, lifted foot)
  * POSES                        pose name -> arm drawing
  * S                            pixel scale (4 -> 160x200)

Screen-left (viewer's left) = "L", screen-right = "R", as in zombie 1.
Air guitar: one arm strums across the belly while the other frets, raises a
fist or throws the horns; the roles swap halfway through the loop.
"""
import os
import sys

import numpy as np
from PIL import Image

S = 4                       # scale factor
W, H = 40, 50               # logical canvas  (x4 = 160 x 200)
CX = 20                     # horizontal centre of the character
GROUND = 48                 # logical row just below the feet (outline row)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "zombie4")

# 16 colours + transparent (index 0). Edit these to recolour the zombie.
PAL = {
    1: (28, 24, 34),      # outline
    2: (74, 92, 86),      # skin dark  (grey mint)
    3: (118, 140, 124),   # skin mid
    4: (160, 180, 150),   # skin light
    5: (56, 56, 72),      # leather dark
    6: (104, 106, 128),   # leather light
    7: (46, 64, 108),     # jeans dark
    8: (78, 104, 152),    # jeans light
    9: (236, 232, 204),   # eye white
    10: (58, 20, 32),     # pupil / mouth
    11: (240, 232, 200),  # teeth / tee shirt
    12: (206, 210, 222),  # silver studs / buckles
    13: (226, 84, 150),   # hair light (hot pink)
    14: (150, 40, 104),   # hair dark
    15: (74, 52, 52),     # boots
    16: (196, 48, 60),    # red: eye veins, shirt print
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

    def image(s):
        a = np.zeros((s.h, s.w, 4), dtype=np.uint8)
        for y in range(s.h):
            for x in range(s.w):
                v = s.g[y][x]
                if v:
                    a[y, x] = (*PAL[v], 255)
        return Image.fromarray(a, "RGBA").resize((s.w * S, s.h * S), Image.NEAREST)


# ------------------------------------------------------------- body parts
def head():
    """Grey-mint face, pink spikes, a stud earring, snarl, and the right eye
    popped out (it bulges past the edge of the head, x 12)."""
    c = C(13, 12)
    rows = {2: (1, 10), 3: (0, 11), 4: (0, 11), 5: (0, 11), 6: (0, 11),
            7: (0, 11), 8: (0, 11), 9: (0, 11), 10: (1, 10), 11: (3, 8)}
    for y, (a, b) in rows.items():
        for x in range(a, b + 1):
            c.set(x, y, 3)
    for y in range(3, 10):
        c.set(0, y, 4)
        c.set(11, y, 2)
    c.set(10, 10, 2)
    c.rect(3, 11, 6, 1, 2)
    # spiky hair: tips, ridge, cap, bangs (light pink left, dark pink right)
    for x in (2, 5, 8):
        c.set(x, 0, 13 if x < 6 else 14)
    c.rect(1, 1, 5, 1, 13)
    c.rect(6, 1, 5, 1, 14)
    c.rect(1, 2, 5, 1, 13)
    c.rect(6, 2, 5, 1, 14)
    c.rect(1, 3, 3, 1, 14)
    c.set(0, 7, 12)                    # earring stud
    # left eye (normal)
    c.rect(2, 4, 3, 3, 9)
    c.rect(3, 5, 1, 2, 10)
    c.rect(2, 7, 3, 1, 2)
    # right eye: popped out, veiny, bigger than the other
    for y, (a, b) in {3: (9, 11), 4: (8, 12), 5: (8, 12), 6: (9, 11)}.items():
        for x in range(a, b + 1):
            c.set(x, y, 9)
    c.rect(10, 4, 2, 2, 10)
    for x, y in ((9, 3), (12, 4), (8, 5), (10, 6)):
        c.set(x, y, 16)
    # nose + snarl
    c.set(5, 7, 2)
    c.set(6, 7, 2)
    c.rect(3, 9, 6, 1, 10)
    c.rect(4, 10, 4, 1, 10)
    for x in (4, 6, 7):
        c.set(x, 9, 11)
    return c


def torso():
    """Black leather jacket with studs, open over a cream band tee."""
    c = C(12, 14)
    c.rect(0, 0, 12, 12, 5)
    c.rect(0, 0, 4, 12, 6)             # lit left lapel
    c.rect(3, 0, 1, 12, 5)             # lapel edge
    c.rect(8, 0, 1, 12, 6)
    c.rect(4, 1, 4, 11, 11)            # tee shirt
    c.rect(4, 0, 4, 1, 2)              # neck
    for x, y in ((5, 4), (6, 4), (5, 5), (6, 5), (5, 6), (6, 6), (4, 5), (7, 5)):
        c.set(x, y, 16)                # red print
    for y in (2, 4, 6, 8):             # studs down both lapels
        c.set(1, y, 12)
        c.set(10, y, 12)
    c.set(0, 0, 12)                    # shoulder studs
    c.set(11, 0, 12)
    c.rect(4, 11, 4, 1, 2)             # waistband gap
    c.rect(5, 11, 2, 1, 12)            # belt buckle
    c.rect(0, 12, 4, 2, 5)             # jacket flaps
    c.rect(8, 12, 4, 2, 5)
    c.rect(0, 12, 1, 2, 6)
    c.rect(4, 12, 4, 1, 11)            # shirt hem
    c.set(5, 13, 11)
    return c


def leg(side, short=0):
    """Ripped blue jeans (knee torn open), buckled boots.
    short = rows removed for a knee bend (total height is 14 - short)."""
    m = 9 - short                      # jeans rows
    c = C(6, 14 - short)
    b = 1 if side == "L" else 0
    c.rect(b, 0, 3, m, 8)
    c.rect(b + 3, 0, 2, m, 7)
    c.rect(b + 1, 4, 3, 2, 3)          # torn knee shows skin
    c.set(b + 1, 5, 2)
    c.set(b, 4, 7)                     # frayed threads
    c.set(b + 4, 5, 8)
    c.rect(b, m, 5, 3, 15)             # boot shaft
    c.rect(0, m + 3, 6, 2, 15)         # boot foot
    c.set(b + 2, m + 1, 12)            # buckle
    c.set(0 if side == "L" else 5, m + 3, 12)   # toe shine
    return c


def popped_eye():
    """The loose eyeball with a bit of nerve."""
    c = C(6, 8)
    for y, (a, b) in {0: (1, 4), 1: (0, 5), 2: (0, 5), 3: (0, 5), 4: (0, 5), 5: (1, 4)}.items():
        for x in range(a, b + 1):
            c.set(x, y, 9)
    c.rect(3, 2, 2, 2, 10)
    for x, y in ((1, 1), (0, 3), (2, 4), (4, 0)):
        c.set(x, y, 16)
    c.set(2, 6, 16)                    # nerve
    c.set(3, 6, 16)
    c.set(3, 7, 2)
    return c


def arm(hy=0, horns=False):
    """Screen-left arm in a studded leather sleeve; returns (canvas, ax, sy).
    ax = local x of the sleeve edge that touches the torso, sy = local row of
    the sleeve top. hy moves the hand up (-) or down (+) from level
    (-9 raised, 0 level, +4 lowered). horns=True throws the rock sign."""
    sy = 14
    c = C(10, 24)
    ht = sy - 1 + hy                   # hand top row
    y0, y1 = min(sy + 1, ht + 2), max(sy + 3, ht + 4)
    c.rect(4, y0, 3, y1 - y0 + 1, 3)   # wrist / forearm
    c.rect(4, y0, 3, 1, 4)
    c.rect(4, y1, 3, 1, 2)
    c.rect(1, ht, 4, 6, 3)             # hand
    c.rect(1, ht, 1, 6, 4)
    c.rect(4, ht, 1, 6, 2)
    c.rect(1, ht + 5, 4, 1, 2)
    if horns:                          # index + pinky up
        c.rect(1, ht - 2, 1, 2, 3)
        c.rect(4, ht - 2, 1, 2, 3)
    else:
        for k in (0, 2, 4):
            c.set(0, ht + k, 3)
        c.rect(2, ht - 1, 2, 1, 3)
    c.rect(4, sy, 6, 4, 5)             # leather sleeve (covers the forearm)
    c.rect(4, sy, 6, 1, 6)
    c.rect(4, sy, 1, 4, 6)
    c.set(6, sy + 2, 12)
    c.set(8, sy + 2, 12)
    return c, 9, sy


def strum_arm(k=0):
    """Air-guitar strumming arm: sleeve bent across the belly, hand over the
    guitar's 'pick' spot. k = extra px down (strum up/down). Built for the
    screen-left side."""
    c = C(8, 14)
    c.rect(2, 4 + k, 4, 4, 5)          # forearm sleeve
    c.rect(2, 4 + k, 4, 1, 6)
    c.set(3, 6 + k, 12)
    c.rect(4, 7 + k, 4, 5, 3)          # hand
    c.rect(4, 7 + k, 1, 5, 4)
    c.rect(7, 7 + k, 1, 5, 2)
    c.rect(4, 11 + k, 4, 1, 2)
    c.set(5, 12 + k, 3)                # fingers
    c.set(7, 12 + k, 3)
    c.rect(0, 0, 4, 4, 5)              # upper sleeve at the shoulder
    c.rect(0, 0, 4, 1, 6)
    c.set(1, 2, 12)
    return c, 3, 0


# ------------------------------------------------------------------ dance
# One row per frame.
#   dx      body shift left/right (logical px, 1 px = 4 real px)
#   tilt    head tilt: how far the top of the head leans (px)
#   bob     torso/head/arms drop by this many px; legs get shorter by the same
#           amount, so the feet stay on the ground. bob 2 = knees bent
#   headdy  head-bang: extra px the head drops (3 = head thrown down)
#   armL/R  pose names, see POSES
#   lift    foot raised 1 px ('L', 'R' or None) = weight on the other foot
DANCE = [
    dict(dx=-2, tilt=-3, bob=0, headdy=-1, armL="strum0", armR="out",    lift="R"),
    dict(dx=-1, tilt=0,  bob=1, headdy=3,  armL="strum2", armR="up",     lift=None),
    dict(dx=0,  tilt=-2, bob=2, headdy=0,  armL="strum0", armR="horns",  lift=None),  # knees bent
    dict(dx=1,  tilt=0,  bob=1, headdy=3,  armL="strum2", armR="out",    lift="L"),
    dict(dx=2,  tilt=3,  bob=0, headdy=-1, armL="horns",  armR="strum0", lift="L"),
    dict(dx=1,  tilt=0,  bob=1, headdy=3,  armL="up",     armR="strum2", lift=None),
    dict(dx=0,  tilt=2,  bob=2, headdy=0,  armL="horns",  armR="strum0", lift=None),  # knees bent
    dict(dx=-1, tilt=0,  bob=1, headdy=3,  armL="out",    armR="strum2", lift="R"),
]
POSES = {
    "out": lambda: arm(0),
    "up": lambda: arm(-6),
    "horns": lambda: arm(-9, horns=True),
    "down": lambda: arm(4),
    "strum0": lambda: strum_arm(0),
    "strum2": lambda: strum_arm(2),
}


def sheared_head(tilt):
    """Head leaning by `tilt` px at the top, pivoting around the chin."""
    h = head()
    o = C(19, 12)
    for r in range(12):
        sh = round(tilt * (11 - r) / 11)
        for i in range(h.w):
            if h.g[r][i]:
                o.set(3 + sh + i, r, h.g[r][i])
    return o


def put_arm(c, drawn, side, dx, bob):
    a, ax, sy = drawn
    oy = 22 + bob - sy                 # shoulder row is 22
    if side == "L":
        c.paste(a, CX - 6 + dx - ax, oy)
    else:
        a = a.flip()
        c.paste(a, CX + 5 + dx - (a.w - 1 - ax), oy)


def frame(f):
    d = DANCE[f]
    dx, bob = d["dx"], d["bob"]
    c = C(W, H)

    # legs: shorter when the knees bend, pushed outward a little at bob 2
    kx = 1 if bob >= 2 else 0
    ly = GROUND - (14 - bob)
    lyL = ly - (1 if d["lift"] == "L" else 0)
    lyR = ly - (1 if d["lift"] == "R" else 0)
    lxL = CX - 7 + dx - kx - (1 if d["lift"] == "L" else 0)
    lxR = CX + 1 + dx + kx + (1 if d["lift"] == "R" else 0)
    c.paste(leg("L", bob), lxL, lyL)
    c.paste(leg("R", bob), lxR, lyR)

    # hips + torso
    c.rect(CX - 6 + dx, 34 + bob, 12, 3, 8)
    c.rect(CX + 2 + dx, 34 + bob, 4, 3, 7)
    c.paste(torso(), CX - 6 + dx, 21 + bob)

    # arms
    put_arm(c, POSES[d["armL"]](), "L", dx, bob)
    put_arm(c, POSES[d["armR"]](), "R", dx, bob)

    # neck + head (banging)
    c.rect(CX - 2 + dx, 20 + bob, 4, 1, 2)
    c.paste(sheared_head(d["tilt"]), CX - 6 + dx - 3, 8 + bob + d["headdy"])

    c.outline()
    return c


# ------------------------------------------------------------------- main
def build_parts():
    """Body-part sprites, each drawn at the same pixel scale as the frames."""
    return {
        "head": head(),
        "torso": torso(),
        "armL": arm(0)[0],
        "armR": arm(0)[0].flip(),
        "legL": leg("L"),
        "legR": leg("R"),
        "extra": popped_eye(),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in range(8):
        frame(f).image().save(os.path.join(OUT, f"zombie4_dance{f}.png"))

    parts = build_parts()
    for name, p in parts.items():
        big = C(p.w + 4, p.h + 4)
        big.paste(p, 2, 2)
        big.outline()
        big.crop(0).image().save(os.path.join(OUT, f"zombie4_{name}.png"))

    # contact sheet (preview only)
    sheet = Image.new("RGBA", (160 * 4 + 50, 200 * 2 + 30 + 80 + 30), (88, 92, 104, 255))
    for i in range(8):
        im = Image.open(os.path.join(OUT, f"zombie4_dance{i}.png"))
        sheet.alpha_composite(im, (10 + (i % 4) * 170, 10 + (i // 4) * 210))
    x = 10
    for name in parts:
        im = Image.open(os.path.join(OUT, f"zombie4_{name}.png"))
        sheet.alpha_composite(im, (x, 440))
        x += im.width + 12
    sheet.save(os.path.join(OUT, "zombie4_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
