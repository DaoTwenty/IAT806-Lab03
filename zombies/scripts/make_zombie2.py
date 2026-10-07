#!/usr/bin/env python3
"""
Zombie 2 (office zombie): 8 dance frames + 7 body parts.

Run:   python3 make_zombie2.py [output_dir]
Needs: pip install pillow numpy
Output (default ./zombie2/):
    zombie2_dance0.png ... zombie2_dance7.png     160x200, transparent
    zombie2_head / torso / armL / armR / legL / legR / extra .png   (<= 64x64)
    zombie2_preview.png                            contact sheet (not part of the set)

Same method as make_zombie1.py: everything is drawn on a 40x50 grid of
"logical pixels" using palette indices, then scaled 4x with nearest-neighbour
(-> 160x200). A 1-logical-pixel outline is added automatically.

Where to change things
  * PAL                          the 16-colour palette (index -> RGB)
  * head() torso() leg() arm() reach_arm() briefcase()    the part drawings
  * the DANCE table              one row per frame (body shift, head tilt,
                                 torso bob, head nod, arm poses, lifted foot)
  * L_POSES / R_POSES            which drawing each arm pose name uses
  * S                            pixel scale (4 -> 160x200)

Screen-left (viewer's left) = "L", screen-right = "R", as in zombie 1.
In this zombie the screen-left hand carries the briefcase, the screen-right
arm is the disco pointer (and the one that has lost its sleeve).
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
    os.path.dirname(os.path.abspath(__file__)), "zombie2")

# 16 colours + transparent (index 0). Edit these to recolour the zombie.
PAL = {
    1: (28, 24, 34),      # outline
    2: (88, 106, 92),     # skin dark  (pale grey-green)
    3: (140, 158, 134),   # skin mid
    4: (178, 192, 166),   # skin light
    5: (176, 182, 204),   # shirt shade
    6: (240, 240, 236),   # shirt white
    7: (36, 38, 52),      # slacks dark
    8: (66, 70, 92),      # slacks light
    9: (236, 232, 204),   # eye white
    10: (58, 20, 32),     # pupil / mouth
    11: (230, 226, 196),  # name tag / clasp
    12: (44, 40, 52),     # shoes / hair
    13: (190, 40, 52),    # tie red
    14: (128, 24, 40),    # tie dark
    15: (146, 98, 56),    # briefcase brown
    16: (98, 62, 36),     # briefcase dark
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
    c = C(12, 12)
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
    # thin combed-over hair
    c.rect(1, 1, 10, 1, 12)
    c.rect(1, 2, 3, 1, 12)
    for x in (5, 8, 9):
        c.set(x, 0, 12)
    # tired, half-lidded eyes with bags and sad brows
    c.rect(2, 4, 3, 1, 2)
    c.rect(7, 4, 3, 1, 2)
    c.rect(2, 5, 3, 2, 9)
    c.rect(7, 5, 3, 2, 9)
    c.set(3, 6, 10)
    c.set(8, 6, 10)
    c.rect(2, 7, 3, 1, 2)
    c.rect(7, 7, 3, 1, 2)
    for x in (3, 4, 7, 8):
        c.set(x, 3, 2)
    # nose, frown, grey cheek blotch
    c.set(5, 7, 2)
    c.set(6, 7, 2)
    c.rect(4, 9, 4, 1, 10)
    c.set(3, 10, 10)
    c.set(8, 10, 10)
    c.rect(9, 8, 2, 2, 2)
    return c


def torso():
    """White shirt torn away on the screen-right side, red loose tie, name tag."""
    c = C(12, 14)
    c.rect(0, 0, 12, 12, 6)
    c.rect(6, 0, 2, 12, 5)
    c.rect(4, 0, 4, 1, 2)              # open collar
    c.rect(5, 1, 2, 1, 2)
    # torn side: skin shows from the ragged edge to the right border
    edge = {3: 10, 4: 9, 5: 10, 6: 8, 7: 9, 8: 8, 9: 9, 10: 8, 11: 9}
    for y, e in edge.items():
        for x in range(e, 12):
            c.set(x, y, 3)
        c.set(11, y, 2)
        c.set(e, y, 4)
    c.rect(8, 11, 4, 1, 2)
    # name tag
    c.rect(1, 4, 3, 2, 11)
    c.set(1, 4, 13)
    c.set(2, 5, 10)
    c.set(3, 5, 10)
    # loose red tie
    c.rect(5, 1, 2, 2, 13)             # knot
    c.rect(5, 3, 2, 5, 13)
    c.rect(6, 3, 1, 5, 14)
    c.rect(5, 8, 3, 3, 13)
    c.rect(7, 8, 1, 3, 14)
    c.rect(6, 11, 2, 1, 14)
    # ragged hem
    for x in (0, 1, 3, 4, 6):
        c.set(x, 12, 6)
    for x in (0, 3):
        c.set(x, 13, 6)
    return c


def leg(side, short=0):
    """Loose dark slacks, grey ankle, black shoe. short = rows removed for a
    knee bend (total height is 14 - short)."""
    m = 10 - short                     # pants rows
    c = C(6, 14 - short)
    b = 1 if side == "L" else 0
    c.rect(b, 0, 3, m, 8)
    c.rect(b + 3, 0, 2, m, 7)
    c.rect(b, m - 1, 5, 1, 7)          # cuff shadow
    c.rect(b + 1, m, 3, 1, 3)          # ankle
    c.set(b + 3, m, 2)
    c.rect(0, m + 1, 6, 3, 12)         # shoe
    c.rect(0, m + 1, 4, 1, 8)
    return c


def briefcase():
    c = C(8, 7)
    c.rect(3, 0, 2, 1, 16)             # handle
    c.set(2, 1, 16)
    c.set(5, 1, 16)
    c.rect(0, 2, 8, 5, 15)             # body
    c.rect(0, 6, 8, 1, 16)
    c.rect(7, 2, 1, 5, 16)
    c.rect(0, 4, 8, 1, 16)             # belt
    c.set(3, 4, 11)                    # clasp
    c.set(4, 4, 11)
    return c


def arm(hy=0, point=None, case=False, torn=False):
    """Screen-left arm held out sideways; returns (canvas, ax, sy).
    ax = local x of the sleeve edge that touches the torso, sy = local row of
    the sleeve top. hy moves the hand up (-) or down (+): 0 level, -9 raised,
    +4 lowered. point = 'up' / 'down' draws a disco index finger.
    case=True hangs the briefcase from the hand. torn=True = shirt sleeve
    ripped off (used for the screen-right arm)."""
    sy = 14
    c = C(10, 29)
    ht = sy - 1 + hy                   # hand top row
    y0, y1 = min(sy + 1, ht + 2), max(sy + 3, ht + 4)
    c.rect(4, y0, 3, y1 - y0 + 1, 3)   # forearm
    c.rect(4, y0, 3, 1, 4)
    c.rect(4, y1, 3, 1, 2)
    c.rect(1, ht, 4, 6, 3)             # hand
    c.rect(1, ht, 1, 6, 4)
    c.rect(4, ht, 1, 6, 2)
    c.rect(1, ht + 5, 4, 1, 2)
    if point == "up":
        c.rect(2, ht - 3, 1, 3, 3)
        c.set(2, ht - 3, 4)
    elif point == "down":
        c.rect(2, ht + 6, 1, 3, 3)
        c.set(2, ht + 8, 2)
    else:
        for k in (0, 2, 4):            # fingers
            c.set(0, ht + k, 3)
        c.rect(2, ht - 1, 2, 1, 3)     # thumb
    if case:
        c.paste(briefcase(), 0, ht + 6)
    if torn:                           # bare shoulder + shirt scrap
        c.rect(6, sy, 4, 4, 3)
        c.rect(6, sy + 3, 4, 1, 2)
        c.rect(8, sy, 2, 2, 6)
        c.set(9, sy + 1, 5)
    else:                              # white sleeve, ragged edge
        c.rect(6, sy, 4, 4, 6)
        c.rect(8, sy, 2, 4, 5)
        c.set(6, sy, 0)
        c.set(6, sy + 3, 0)
    return c, 9, sy


def reach_arm(torn=False):
    """Classic zombie reach: the arm widens toward the hand (sleeve 4 px,
    forearm 5 px, hand 5x7 px) so it reads as stretching toward the viewer."""
    c = C(12, 14)
    c.rect(4, 5, 5, 5, 3)              # forearm
    c.rect(4, 5, 5, 1, 4)
    c.rect(4, 9, 5, 1, 2)
    c.rect(0, 1, 5, 7, 3)              # big hand
    c.rect(0, 1, 1, 7, 4)
    c.rect(4, 1, 1, 7, 2)
    c.rect(0, 7, 5, 1, 2)
    for x in (0, 2, 4):                # fingers up
        c.set(x, 0, 3)
    c.set(5, 6, 3)                     # thumb
    if torn:
        c.rect(8, 8, 4, 4, 3)
        c.rect(8, 11, 4, 1, 2)
        c.rect(10, 8, 2, 2, 6)
    else:
        c.rect(8, 8, 4, 4, 6)
        c.rect(10, 8, 2, 4, 5)
    return c, 11, 8


# ------------------------------------------------------------------ dance
# One row per frame.
#   dx      body shift left/right (logical px, 1 px = 4 real px)
#   tilt    head tilt: how far the top of the head leans (px)
#   bob     torso/head/arms drop by this many px; legs get shorter by the same
#           amount, so the feet stay on the ground. bob 2 = knees bent
#   headdy  extra head nod (px down) on top of bob
#   armL    briefcase arm:  'case' (hand low) | 'case_hi' (hand level)
#   armR    pointing arm:   'up' | 'down' | 'reach'
#   lift    foot raised 1 px ('L', 'R' or None) = weight on the other foot
DANCE = [
    dict(dx=-2, tilt=-3, bob=0, headdy=0, armL="case",    armR="up",    lift="R"),
    dict(dx=-1, tilt=-2, bob=1, headdy=1, armL="case_hi", armR="down",  lift=None),
    dict(dx=0,  tilt=-1, bob=2, headdy=1, armL="case",    armR="up",    lift=None),  # knees bent
    dict(dx=1,  tilt=2,  bob=1, headdy=0, armL="case_hi", armR="reach", lift="L"),
    dict(dx=2,  tilt=3,  bob=0, headdy=0, armL="case",    armR="up",    lift="L"),
    dict(dx=1,  tilt=2,  bob=1, headdy=1, armL="case_hi", armR="down",  lift=None),
    dict(dx=0,  tilt=1,  bob=2, headdy=1, armL="case",    armR="up",    lift=None),  # knees bent
    dict(dx=-1, tilt=-2, bob=1, headdy=0, armL="case_hi", armR="reach", lift="R"),
]
# pose name -> drawing (returns canvas, ax, sy); the R arm is mirrored later
L_POSES = {
    "case": lambda: arm(3, case=True),
    "case_hi": lambda: arm(0, case=True),
}
R_POSES = {
    "up": lambda: arm(-9, point="up", torn=True),
    "down": lambda: arm(4, point="down", torn=True),
    "reach": lambda: reach_arm(torn=True),
}


def sheared_head(tilt):
    """Head leaning by `tilt` px at the top, pivoting around the chin."""
    h = head()
    o = C(18, 12)
    for r in range(12):
        sh = round(tilt * (11 - r) / 11)
        for i in range(12):
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
    put_arm(c, L_POSES[d["armL"]](), "L", dx, bob)
    put_arm(c, R_POSES[d["armR"]](), "R", dx, bob)

    # neck + head (tilted, nodding)
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
        "armL": arm(0)[0],                       # open hand, shirt sleeve
        "armR": arm(0, torn=True)[0].flip(),     # ripped sleeve
        "legL": leg("L"),
        "legR": leg("R"),
        "extra": briefcase(),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in range(8):
        frame(f).image().save(os.path.join(OUT, f"zombie2_dance{f}.png"))

    parts = build_parts()
    for name, p in parts.items():
        big = C(p.w + 4, p.h + 4)
        big.paste(p, 2, 2)
        big.outline()
        big.crop(0).image().save(os.path.join(OUT, f"zombie2_{name}.png"))

    # contact sheet (preview only)
    sheet = Image.new("RGBA", (160 * 4 + 50, 200 * 2 + 30 + 80 + 30), (88, 92, 104, 255))
    for i in range(8):
        im = Image.open(os.path.join(OUT, f"zombie2_dance{i}.png"))
        sheet.alpha_composite(im, (10 + (i % 4) * 170, 10 + (i // 4) * 210))
    x = 10
    for name in parts:
        im = Image.open(os.path.join(OUT, f"zombie2_{name}.png"))
        sheet.alpha_composite(im, (x, 440))
        x += im.width + 12
    sheet.save(os.path.join(OUT, "zombie2_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
