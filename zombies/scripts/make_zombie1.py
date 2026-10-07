#!/usr/bin/env python3
"""
Zombie 1 (classic shambler): 8 dance frames + 7 body parts.

Run:   python3 make_zombie1.py [output_dir]
Needs: pip install pillow numpy
Output (default ./zombie1/):
    zombie1_dance0.png ... zombie1_dance7.png     160x200, transparent
    zombie1_head / torso / armL / armR / legL / legR / extra .png   (<= 64x64)
    zombie1_preview.png                            contact sheet (not part of the set)

How it works
------------
Everything is drawn on a 40x50 "logical pixel" grid using palette indices,
then scaled 4x with nearest-neighbour (-> 160x200), so every sprite pixel is a
crisp 4x4 block. A 1-logical-pixel outline is added automatically around the
silhouette (outline()).

Things you will most likely want to edit
  * PAL                      the 15-colour palette (index -> RGB)
  * head() torso() leg() arm() reach_arm() extra_hand()   the body-part drawings
  * the DANCE table below    one row per frame: body shift, head tilt, bob,
                             arm poses, which foot is lifted
  * S                        pixel scale (4 -> 160x200)
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
    os.path.dirname(os.path.abspath(__file__)), "zombie1")

# 15 colours + transparent (index 0)
PAL = {
    1: (28, 24, 34),      # outline
    2: (70, 104, 70),     # skin dark
    3: (108, 150, 94),    # skin mid
    4: (150, 186, 116),   # skin light
    5: (122, 50, 56),     # shirt dark
    6: (170, 86, 80),     # shirt light
    7: (48, 56, 92),      # pants dark
    8: (82, 96, 138),     # pants light
    9: (236, 232, 204),   # eye white
    10: (58, 20, 32),     # pupil / mouth
    11: (246, 240, 212),  # teeth / bone
    12: (72, 50, 42),     # shoe
    13: (128, 120, 70),   # rot patch
    14: (40, 48, 36),     # hair
    15: (110, 84, 70),    # shoe highlight
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
    # messy hair
    c.rect(1, 1, 10, 1, 14)
    for x in (1, 3, 6, 8, 10):
        c.set(x, 0, 14)
    c.rect(1, 2, 2, 1, 14)
    c.rect(8, 2, 3, 1, 13)             # rot patch
    # brows, eyes, bags
    c.rect(2, 3, 3, 1, 2)
    c.rect(7, 3, 3, 1, 2)
    c.rect(2, 4, 3, 3, 9)
    c.rect(7, 4, 3, 3, 9)
    c.rect(4, 5, 1, 2, 10)             # derpy pupils
    c.rect(7, 4, 1, 2, 10)
    c.rect(2, 7, 3, 1, 2)
    c.rect(7, 7, 3, 1, 2)
    # nose
    c.set(5, 7, 2)
    c.set(6, 7, 2)
    # mouth + two teeth
    c.rect(3, 9, 6, 1, 10)
    c.rect(4, 10, 4, 1, 10)
    c.set(4, 9, 11)
    c.set(7, 9, 11)
    return c


def torso():
    c = C(12, 14)
    c.rect(0, 0, 12, 12, 6)
    c.rect(8, 0, 4, 12, 5)
    c.rect(3, 0, 6, 1, 2)              # collar hole
    c.rect(4, 1, 4, 1, 2)
    # belly tear with a rib showing
    c.rect(3, 6, 3, 1, 3)
    c.set(2, 7, 3)
    c.rect(3, 7, 2, 1, 11)
    c.set(5, 7, 3)
    c.rect(2, 8, 3, 1, 2)
    # ragged hem
    for x in (0, 1, 4, 5, 9, 10, 11):
        c.set(x, 12, 6 if x < 8 else 5)
    for x in (0, 4, 10):
        c.set(x, 13, 6 if x < 8 else 5)
    return c


def leg(side, short=0):
    """side 'L' = screen-left leg, 'R' = screen-right leg.
    short = rows of pants removed (knee bend); total height is 14 - short."""
    n = 8 - short                      # pants rows
    c = C(6, 14 - short)
    b = 1 if side == "L" else 0
    c.rect(b + 1, n, 3, 3, 3)          # shin
    c.rect(b + 3, n, 1, 3, 2)
    c.rect(b, 0, 3, n, 8)              # pants
    c.rect(b + 3, 0, 2, n, 7)
    c.rect(b + 1, 4, 2, 1, 3)          # knee tear
    for x in (0, 2, 4):                # ragged cuff
        c.set(b + x, n, 8 if x < 3 else 7)
    c.rect(0, n + 3, 6, 3, 12)         # shoe
    c.rect(0, n + 3, 4, 1, 15)
    return c


def arm(hy=0):
    """Screen-left arm, shoulder on the right edge, held out sideways.
    hy = how far the hand is moved up (negative) or down (positive):
    0 = level, -6 = raised, +4 = lowered. hy=0 is the arm used for the
    armL / armR body-part sprites."""
    c = C(10, 17)
    ht = 7 + hy                        # hand top row
    y0, y1 = min(9, ht + 2), max(11, ht + 4)
    c.rect(4, y0, 3, y1 - y0 + 1, 3)   # forearm
    c.rect(4, y0, 3, 1, 4)
    c.rect(4, y1, 3, 1, 2)
    c.rect(1, ht, 4, 6, 3)             # hand (bigger than the forearm)
    c.rect(1, ht, 1, 6, 4)
    c.rect(4, ht, 1, 6, 2)
    c.rect(1, ht + 5, 4, 1, 2)
    for k in (0, 2, 4):                # fingers
        c.set(0, ht + k, 3)
    c.rect(2, ht - 1, 2, 1, 3)         # thumb
    c.rect(6, 8, 4, 4, 6)              # sleeve, drawn last (ragged edge)
    c.rect(8, 8, 2, 4, 5)
    c.set(6, 8, 0)
    c.set(6, 11, 0)
    return c


def reach_arm():
    """Screen-left arm of the classic zombie reach: the hand comes forward
    in front of the chest (bigger, to read as closer to the viewer)."""
    c = C(8, 9)
    c.rect(0, 3, 4, 4, 6)              # sleeve at the shoulder (behind the hand)
    c.rect(2, 3, 2, 4, 5)
    c.set(0, 3, 0)
    c.rect(2, 3, 4, 5, 3)              # hand held in front of the shoulder
    c.rect(2, 3, 1, 5, 4)
    c.rect(5, 3, 1, 5, 2)
    c.rect(2, 7, 4, 1, 2)
    c.set(2, 2, 3)                     # fingers pointing up
    c.set(4, 2, 3)
    c.set(5, 2, 3)
    c.set(3, 1, 3)
    c.set(4, 1, 3)
    c.rect(3, 5, 2, 1, 2)              # knuckle line
    return c


def extra_hand():
    c = C(7, 9)
    for x in (0, 2, 4, 6):             # fingers
        c.rect(x, 0, 1, 2, 3)
    c.rect(0, 2, 7, 4, 3)
    c.rect(0, 2, 1, 4, 4)
    c.rect(6, 2, 1, 4, 2)
    c.rect(0, 5, 7, 1, 2)
    c.rect(1, 6, 5, 2, 3)              # wrist stump
    c.rect(5, 6, 1, 2, 2)
    c.set(3, 7, 11)                    # bone
    c.set(2, 8, 2)
    c.set(4, 8, 2)
    c.set(3, 8, 11)
    c.set(5, 7, 0)
    return c


# ------------------------------------------------------------------ dance
# One row per frame.
#   dx      body shift left/right (logical px, 1 px = 4 real px)
#   tilt    head tilt: how far the top of the head leans (px)
#   bob     torso/head/arms drop by this many px; legs get shorter by the same
#           amount, so the feet never leave the ground. bob 2 = knees bent
#   armL/R  'up' | 'out' | 'down' | 'reach'   (screen-left / screen-right arm)
#   lift    foot raised 1 px ('L', 'R' or None) = weight on the other foot
#   rdy     extra vertical offset (L, R) of the reaching hands, for wobble
DANCE = [
    dict(dx=-2, tilt=-3, bob=0, armL="up",    armR="down",  lift="R", rdy=(0, 0)),
    dict(dx=-1, tilt=-2, bob=1, armL="reach", armR="reach", lift=None, rdy=(0, 1)),
    dict(dx=0,  tilt=-1, bob=2, armL="down",  armR="up",    lift=None, rdy=(0, 0)),  # knees bent
    dict(dx=1,  tilt=2,  bob=1, armL="out",   armR="out",   lift="L", rdy=(0, 0)),
    dict(dx=2,  tilt=3,  bob=0, armL="down",  armR="up",    lift="L", rdy=(0, 0)),
    dict(dx=1,  tilt=2,  bob=1, armL="reach", armR="reach", lift=None, rdy=(1, 0)),
    dict(dx=0,  tilt=1,  bob=2, armL="up",    armR="down",  lift=None, rdy=(0, 0)),  # knees bent
    dict(dx=-1, tilt=-2, bob=1, armL="out",   armR="out",   lift="R", rdy=(0, 0)),
]
HAND_DY = {"up": -6, "out": 0, "down": 4}


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
    for side, pose in (("L", d["armL"]), ("R", d["armR"])):
        if pose == "reach":
            a = reach_arm()
            ydy = d["rdy"][0 if side == "L" else 1]
            if side == "L":
                c.paste(a, 12 + dx, 19 + bob + ydy)
            else:
                c.paste(a.flip(), 20 + dx, 19 + bob + ydy)
        else:
            a = arm(HAND_DY[pose])
            if side == "L":
                c.paste(a, 5 + dx, 14 + bob)
            else:
                c.paste(a.flip(), 25 + dx, 14 + bob)

    # neck + tilted head
    c.rect(CX - 2 + dx, 20 + bob, 4, 1, 2)
    c.paste(sheared_head(d["tilt"]), CX - 6 + dx - 3, 8 + bob)

    c.outline()
    return c


# ------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    for f in range(8):
        frame(f).image().save(os.path.join(OUT, f"zombie1_dance{f}.png"))

    parts = {
        "head": head(), "torso": torso(),
        "armL": arm(), "armR": arm().flip(),
        "legL": leg("L"), "legR": leg("R"),
        "extra": extra_hand(),
    }
    for name, p in parts.items():
        big = C(p.w + 4, p.h + 4)
        big.paste(p, 2, 2)
        big.outline()
        big.crop(0).image().save(os.path.join(OUT, f"zombie1_{name}.png"))

    # contact sheet (preview only)
    sheet = Image.new("RGBA", (160 * 4 + 50, 200 * 2 + 30 + 80 + 30), (88, 92, 104, 255))
    for i in range(8):
        im = Image.open(os.path.join(OUT, f"zombie1_dance{i}.png"))
        sheet.alpha_composite(im, (10 + (i % 4) * 170, 10 + (i // 4) * 210))
    x = 10
    for name in parts:
        im = Image.open(os.path.join(OUT, f"zombie1_{name}.png"))
        sheet.alpha_composite(im, (x, 440))
        x += im.width + 12
    sheet.save(os.path.join(OUT, "zombie1_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
