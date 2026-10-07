#!/usr/bin/env python3
"""
Zombie 3 (zombie cheerleader): 8 dance frames + 7 body parts.

Run:   python3 make_zombie3.py [output_dir]
Needs: pip install pillow numpy
Output (default ./zombie3/):
    zombie3_dance0.png ... zombie3_dance7.png     160x200, transparent
    zombie3_head / torso / armL / armR / legL / legR / extra .png   (<= 64x64)
    zombie3_preview.png                            contact sheet (not part of the set)

Same method as make_zombie1.py: everything is drawn on a 40x50 grid of
"logical pixels" using palette indices, then scaled 4x with nearest-neighbour
(-> 160x200). A 1-logical-pixel outline is added automatically.

Where to change things
  * PAL                          the 15-colour palette (index -> RGB)
  * head() torso() leg() kick_leg() arm() pom()    the part drawings
  * the DANCE table              one row per frame (body shift, head tilt,
                                 torso bob, arm poses, lifted foot, kick)
  * ARM_POSES                    hand height for each arm pose name
  * S                            pixel scale (4 -> 160x200)

Screen-left (viewer's left) = "L", screen-right = "R", as in zombie 1.
The kick happens on frames 3 (screen-right leg) and 7 (screen-left leg).
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
    os.path.dirname(os.path.abspath(__file__)), "zombie3")

# 15 colours + transparent (index 0). Edit these to recolour the zombie.
PAL = {
    1: (28, 24, 34),      # outline
    2: (84, 122, 156),    # skin dark  (pale blue)
    3: (132, 174, 204),   # skin mid
    4: (178, 210, 228),   # skin light
    5: (150, 34, 52),     # red dark
    6: (214, 66, 72),     # red light
    7: (186, 192, 212),   # white shade
    8: (242, 240, 234),   # white
    9: (236, 232, 204),   # eye white
    10: (58, 20, 32),     # pupil / mouth
    11: (156, 104, 170),  # hair light
    12: (96, 56, 116),    # hair dark
    13: (226, 110, 140),  # tongue
    14: (244, 206, 84),   # pom-pom gold
    15: (200, 148, 52),   # pom-pom gold shade
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
    """Pale blue face, messy purple hair, ponytail hanging on the screen-right
    side (x 12..13), lolling tongue. Canvas is 14 wide so the part sprite
    stays within 64 px."""
    c = C(14, 12)
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
    # messy hair on top
    for x in (2, 4, 5, 7, 9):
        c.set(x, 0, 12)
    c.set(3, 0, 11)
    c.set(8, 0, 11)
    c.rect(1, 1, 10, 1, 12)
    for x in (4, 5, 8):
        c.set(x, 1, 11)
    c.rect(1, 2, 4, 1, 12)
    c.set(7, 2, 12)
    c.set(8, 2, 12)
    c.set(11, 2, 12)
    c.set(11, 3, 12)
    c.set(11, 4, 12)
    # ponytail with a red scrunchie
    c.rect(12, 2, 2, 2, 5)
    c.set(12, 2, 6)
    c.rect(12, 4, 2, 6, 12)
    c.set(12, 4, 11)
    c.set(12, 6, 11)
    c.set(13, 8, 11)
    c.set(12, 10, 12)
    c.set(13, 11, 12)
    # big eyes with a lash flick
    c.rect(2, 4, 3, 3, 9)
    c.rect(7, 4, 3, 3, 9)
    c.rect(3, 5, 1, 2, 10)
    c.rect(8, 5, 1, 2, 10)
    c.set(1, 3, 10)
    c.set(10, 3, 10)
    c.set(5, 7, 2)
    c.set(6, 7, 2)
    # red lipstick grin, teeth, lolling tongue
    c.rect(3, 9, 6, 1, 5)
    c.set(4, 9, 8)
    c.set(7, 9, 8)
    c.rect(4, 10, 4, 1, 10)
    c.rect(6, 10, 2, 1, 13)
    c.set(7, 11, 13)
    return c


def torso():
    """Red top with white trim and a Z, bare midriff, torn pleated skirt."""
    c = C(12, 14)
    c.rect(0, 0, 12, 7, 6)
    c.rect(8, 0, 4, 7, 5)
    c.rect(3, 0, 6, 1, 2)              # neckline
    c.rect(4, 1, 4, 1, 2)
    c.rect(0, 6, 12, 1, 8)             # white trim
    for x, y in ((4, 2), (5, 2), (6, 2), (6, 3), (5, 4), (4, 5), (5, 5), (6, 5)):
        c.set(x, y, 8)                 # the Z
    c.rect(1, 7, 10, 2, 3)             # midriff
    c.rect(1, 7, 1, 2, 4)
    c.rect(10, 7, 1, 2, 2)
    c.set(5, 8, 2)
    c.rect(0, 9, 12, 1, 8)             # waistband
    for y in range(10, 14):            # pleats
        for x in range(12):
            c.set(x, y, 6 if (x // 2) % 2 == 0 else 5)
    for x, y in ((3, 13), (4, 13), (8, 13), (9, 13), (6, 12), (0, 13), (11, 13)):
        c.set(x, y, 0)                 # torn hem
    return c


def leg(side, short=0):
    """Pale blue leg, white sock with red stripe, white sneaker.
    short = rows removed for a knee bend (total height is 14 - short)."""
    n = 9 - short                      # skin rows
    c = C(6, 14 - short)
    b = 1 if side == "L" else 0
    c.rect(b, 0, 5, n, 3)
    c.rect(b, 0, 1, n, 4)
    c.rect(b + 4, 0, 1, n, 2)
    c.rect(b, n, 5, 1, 5)              # red sock stripe
    c.rect(b, n + 1, 5, 1, 8)
    c.rect(0, n + 2, 6, 3, 8)          # sneaker
    c.rect(0, n + 4, 6, 1, 7)
    if side == "R":
        c.rect(4, n + 3, 2, 1, 5)
    else:
        c.rect(0, n + 3, 2, 1, 5)
    return c


def kick_leg(side):
    """High side kick, drawn as a staircase going up and out from the hip.
    Built for the screen-left leg; the right one is the mirror image."""
    c = C(12, 11)
    c.rect(6, 8, 6, 3, 3)              # thigh
    c.rect(6, 8, 6, 1, 4)
    c.rect(6, 10, 6, 1, 2)
    c.rect(3, 5, 4, 3, 3)              # shin
    c.rect(3, 5, 4, 1, 4)
    c.rect(3, 7, 4, 1, 2)
    c.rect(1, 3, 3, 1, 5)              # sock
    c.rect(1, 4, 3, 2, 8)
    c.rect(0, 0, 4, 3, 8)              # sneaker
    c.rect(0, 2, 4, 1, 7)
    c.rect(0, 0, 2, 2, 5)
    return c if side == "L" else c.flip()


def pom(w=9, h=8):
    """Pom-pom: red / white / gold streamers in a ragged ball."""
    c = C(w, h)
    mid = w // 2
    half = [2, 3, 4, 4, 4, 4, 3, 2]
    cols = (6, 8, 14)
    dark = {6: 5, 8: 7, 14: 15}
    for r in range(h):
        a = half[r] if r < len(half) else 2
        for x in range(mid - a, mid + a + 1):
            if r == 0 and x % 2 == 1:
                continue
            if r == h - 1 and x % 2 == 0:
                continue
            col = cols[x % 3]
            if r >= h - 2:
                col = dark[col]
            c.set(x, r, col)
    return c


def arm(hy=0, with_pom=True):
    """Screen-left arm; returns (canvas, ax, sy).
    ax = local x of the sleeve edge that touches the torso, sy = local row of
    the sleeve top. hy moves the hand up (-) or down (+) from level.
    with_pom=False gives the bare arm used for the body-part sprites."""
    sy = 14
    c = C(14, 24)
    ht = sy - 1 + hy                   # hand top row
    y0, y1 = min(sy + 1, ht + 2), max(sy + 3, ht + 4)
    c.rect(8, y0, 3, y1 - y0 + 1, 3)   # forearm
    c.rect(8, y0, 3, 1, 4)
    c.rect(8, y1, 3, 1, 2)
    c.rect(5, ht, 4, 6, 3)             # hand
    c.rect(5, ht, 1, 6, 4)
    c.rect(8, ht, 1, 6, 2)
    c.rect(5, ht + 5, 4, 1, 2)
    if with_pom:
        c.paste(pom(), 2, ht - 2)
    else:
        for k in (0, 2, 4):            # fingers
            c.set(4, ht + k, 3)
        c.rect(6, ht - 1, 2, 1, 3)     # thumb
    c.rect(10, sy, 4, 4, 6)            # short red sleeve with white cuff
    c.rect(12, sy, 2, 4, 5)
    c.rect(10, sy + 3, 4, 1, 8)
    c.set(10, sy, 0)
    return c, 13, sy


# ------------------------------------------------------------------ dance
# One row per frame.
#   dx      body shift left/right (logical px, 1 px = 4 real px)
#   tilt    head tilt: how far the top of the head leans (px)
#   bob     torso/head/arms drop by this many px; legs get shorter by the same
#           amount, so the feet stay on the ground. bob 2 = knees bent
#   armL/R  'up' | 'vee' | 'out' | 'down'   (see ARM_POSES)
#   lift    foot raised 1 px ('L', 'R' or None) = weight on the other foot
#   kick    'L' / 'R' = that leg does a high side kick (frames 3 and 7)
DANCE = [
    dict(dx=-1, tilt=-2, bob=0, armL="up",   armR="down", lift="R",  kick=None),
    dict(dx=0,  tilt=-1, bob=1, armL="out",  armR="vee",  lift=None, kick=None),
    dict(dx=0,  tilt=0,  bob=2, armL="down", armR="up",   lift=None, kick=None),  # knees bent
    dict(dx=-1, tilt=3,  bob=0, armL="vee",  armR="out",  lift=None, kick="R"),   # KICK
    dict(dx=1,  tilt=2,  bob=0, armL="down", armR="up",   lift="L",  kick=None),
    dict(dx=1,  tilt=1,  bob=1, armL="vee",  armR="out",  lift=None, kick=None),
    dict(dx=0,  tilt=0,  bob=2, armL="up",   armR="down", lift=None, kick=None),  # knees bent
    dict(dx=1,  tilt=-3, bob=0, armL="out",  armR="vee",  lift=None, kick="L"),   # KICK
]
ARM_POSES = {"up": -8, "vee": -4, "out": 0, "down": 4}   # pose -> hand offset


def sheared_head(tilt):
    """Head leaning by `tilt` px at the top, pivoting around the chin."""
    h = head()
    o = C(20, 12)
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
    if d["kick"] == "L":
        c.paste(kick_leg("L"), 6 + dx, 26 + bob)
    else:
        c.paste(leg("L", bob), lxL, lyL)
    if d["kick"] == "R":
        c.paste(kick_leg("R"), 22 + dx, 26 + bob)
    else:
        c.paste(leg("R", bob), lxR, lyR)

    # hips + torso (the skirt is part of the torso sprite)
    c.rect(CX - 6 + dx, 34 + bob, 12, 3, 3)
    c.rect(CX + 2 + dx, 34 + bob, 4, 3, 2)
    c.paste(torso(), CX - 6 + dx, 21 + bob)

    # arms with pom-poms
    put_arm(c, arm(ARM_POSES[d["armL"]]), "L", dx, bob)
    put_arm(c, arm(ARM_POSES[d["armR"]]), "R", dx, bob)

    # neck + tilted head
    c.rect(CX - 2 + dx, 20 + bob, 4, 1, 2)
    c.paste(sheared_head(d["tilt"]), CX - 6 + dx - 3, 8 + bob)

    c.outline()
    return c


# ------------------------------------------------------------------- main
def build_parts():
    """Body-part sprites, each drawn at the same pixel scale as the frames."""
    return {
        "head": head(),
        "torso": torso(),
        "armL": arm(0, with_pom=False)[0],
        "armR": arm(0, with_pom=False)[0].flip(),
        "legL": leg("L"),
        "legR": leg("R"),
        "extra": pom(),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in range(8):
        frame(f).image().save(os.path.join(OUT, f"zombie3_dance{f}.png"))

    parts = build_parts()
    for name, p in parts.items():
        big = C(p.w + 4, p.h + 4)
        big.paste(p, 2, 2)
        big.outline()
        big.crop(0).image().save(os.path.join(OUT, f"zombie3_{name}.png"))

    # contact sheet (preview only)
    sheet = Image.new("RGBA", (160 * 4 + 50, 200 * 2 + 30 + 80 + 30), (88, 92, 104, 255))
    for i in range(8):
        im = Image.open(os.path.join(OUT, f"zombie3_dance{i}.png"))
        sheet.alpha_composite(im, (10 + (i % 4) * 170, 10 + (i // 4) * 210))
    x = 10
    for name in parts:
        im = Image.open(os.path.join(OUT, f"zombie3_{name}.png"))
        sheet.alpha_composite(im, (x, 440))
        x += im.width + 12
    sheet.save(os.path.join(OUT, "zombie3_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
