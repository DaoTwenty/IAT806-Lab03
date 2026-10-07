#!/usr/bin/env python3
"""
make_grenade.py - pixel-art grenade sprite set (grenade, pin, 8 spin frames,
8 explosion frames, preview sheet).

Usage:   python3 make_grenade.py [output_dir]      (default: ./grenade next to this script)
Needs:   Pillow + numpy only.

HOW IT IS BUILT (same idea as the zombie scripts)
  * Everything is drawn on a small LOGICAL pixel grid (class C, palette indices),
    then scaled S x with nearest-neighbour -> chunky hard-edged pixels.
  * The dark outline is added automatically around whatever is filled in (C.outline).
  * Every output pixel is alpha 0 or 255. No blur, gradients, anti-aliasing.

WHERE TO CHANGE THINGS
  * Colors ............. the PALETTE block right below (named colors, defined once).
  * Sizes / frame counts  the SETTINGS block right below.
  * Grenade shape ...... build_fill(): BODY_* numbers (shape), SEG_* (segment grid),
                         cap / neck / lever / ring code.
  * Spin ............... spin_frame(): the grenade is re-sampled per angle (see there).
  * Explosion shape .... explosion_frame(): the per-frame recipes, LUMP_* (how bumpy
                         the fireball is) and EMBERS (the flying sparks).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------
# SETTINGS - change sizes and frame counts here
# ----------------------------------------------------------------------------
S = 4                      # every logical pixel becomes S x S real pixels
GREN_W, GREN_H = 16, 20    # grenade sprite in logical pixels (-> 64 x 80 px), outline included
SPIN_FRAMES = 8            # number of spin frames (angle step = 360 / SPIN_FRAMES)
SPIN_W, SPIN_H = 28, 28    # spin canvas in logical pixels (112 x 112 px); must hold the
                           # grenade at every angle, so it is larger than 16 x 20
SPIN_WITH_PIN = False      # spin the pin-pulled grenade (True = spin the pinned one)
EXPL_PX = 192              # explosion frame size in real pixels (square)
EXPL_FRAMES = 8            # number of explosion frames (the recipes below are written for 8)
EXPL_BLOCK = 2             # explosion is built from BLOCK x BLOCK logical-pixel blocks
                           # (bigger = chunkier circles)

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "grenade")

# ----------------------------------------------------------------------------
# PALETTE - defined once. 12 colors. Change the RGB values to recolor everything.
# ----------------------------------------------------------------------------
OUTLINE, OLIVE_DEEP, OLIVE_DARK, OLIVE_MID, OLIVE_LIGHT, WHITE, YELLOW, \
    ORANGE, RED, DARK_RED, GREY, DARK_GREY = range(1, 13)

PAL = {
    OUTLINE:     (24, 18, 28),      # dark outline
    OLIVE_DEEP:  (36, 50, 30),      # grenade: darkest olive (top, grid lines in shadow)
    OLIVE_DARK:  (62, 86, 40),      # grenade: shadow tone
    OLIVE_MID:   (94, 124, 52),     # grenade: main body tone
    OLIVE_LIGHT: (140, 170, 80),    # grenade: highlight
    WHITE:       (252, 250, 238),   # metal glint + explosion flash
    YELLOW:      (255, 216, 64),    # explosion
    ORANGE:      (255, 140, 32),    # explosion
    RED:         (222, 58, 36),     # explosion
    DARK_RED:    (140, 32, 38),     # explosion rim / cooling embers
    GREY:        (152, 152, 164),   # metal (lever, pin, cap) and light smoke
    DARK_GREY:   (74, 72, 88),      # metal shadow and dark smoke
}

LUT = np.zeros((len(PAL) + 1, 4), dtype=np.uint8)
for _i, _c in PAL.items():
    LUT[_i] = (*_c, 255)          # index 0 stays (0,0,0,0) = transparent


class C:
    """Canvas of palette indices on the logical grid (0 = transparent)."""

    def __init__(s, w, h):
        s.w, s.h = w, h
        s.g = [[0] * w for _ in range(h)]

    def set(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.g[y][x] = c

    def get(s, x, y):
        return s.g[y][x] if 0 <= x < s.w and 0 <= y < s.h else 0

    def rect(s, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                s.set(xx, yy, c)

    def paste(s, o, ox, oy):
        for y in range(o.h):
            for x in range(o.w):
                if o.g[y][x]:
                    s.set(ox + x, oy + y, o.g[y][x])

    def outline(s):
        """One logical pixel of OUTLINE around every filled pixel (4-neighbour)."""
        add = []
        for y in range(s.h):
            for x in range(s.w):
                if s.g[y][x] == 0 and any(
                        s.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add.append((x, y))
        for x, y in add:
            s.g[y][x] = OUTLINE

    def image(s, scale=S):
        arr = LUT[np.array(s.g, dtype=np.uint8)]
        return Image.fromarray(arr, "RGBA").resize((s.w * scale, s.h * scale), Image.NEAREST)


# ----------------------------------------------------------------------------
# GRENADE SHAPE - everything is drawn on a 14 x 18 "fill" grid (no outline); the
# outline is added afterwards, which gives the 16 x 20 sprite.
# ----------------------------------------------------------------------------
FILL_W, FILL_H = GREN_W - 2, GREN_H - 2

# Body: a slightly squared egg. Centre/radii in fill-grid pixels, P = squareness
# (2 = ellipse, bigger = squarer shoulders).
BODY_CX, BODY_CY = 6.5, 11.5
BODY_RX, BODY_RY, BODY_P = 5.7, 6.9, 2.4
# Segment grid: a dark line every SEG_W columns / SEG_H rows.
SEG_W, SEG_OX = 4, 2
SEG_H, SEG_OY = 4, 0
TOP_ROWS = 6               # body rows 0..TOP_ROWS (fill grid) get the darkest "top" tone

# Lever (spoon) as a polyline of fill-grid points; each point is drawn 2 pixels wide.
LEVER_REST = [(9, 2), (10, 3), (11, 4), (12, 5), (12, 6), (12, 7), (12, 8), (12, 9),
              (12, 10), (12, 11), (12, 12), (11, 13)]
# Pin pulled: the hinge stays, the lower end swings one pixel outwards.
LEVER_LIFTED = [(9, 2), (10, 3), (11, 4), (12, 5), (12, 6), (13, 7), (13, 8), (13, 9),
                (13, 10), (13, 11), (13, 12), (12, 13)]

# Pin ring (4 x 4, hollow) at the top left, plus the shaft that goes through the neck.
RING = [(1, 0, WHITE), (2, 0, GREY), (0, 1, WHITE), (3, 1, GREY),
        (0, 2, GREY), (3, 2, DARK_GREY), (1, 3, GREY), (2, 3, DARK_GREY)]


def metal_cap(c):
    """Fuse head on top (metal)."""
    for x, col in zip(range(5, 8), (WHITE, GREY, GREY)):
        c.set(x, 0, col)
    for x, col in zip(range(4, 9), (WHITE, GREY, GREY, GREY, DARK_GREY)):
        c.set(x, 1, col)
    for x, col in zip(range(4, 9), (GREY, GREY, GREY, DARK_GREY, DARK_GREY)):
        c.set(x, 2, col)


def body(c):
    shade = [OLIVE_DEEP, OLIVE_DARK, OLIVE_MID, OLIVE_LIGHT]
    for y in range(c.h):
        for x in range(c.w):
            nx = (x + .5 - BODY_CX) / BODY_RX
            ny = (y + .5 - BODY_CY) / BODY_RY
            if abs(nx) ** BODY_P + abs(ny) ** BODY_P > 1:
                continue
            nz = math.sqrt(max(0.0, 1 - min(1.0, nx * nx + ny * ny)))
            lit = -0.55 * nx - 0.75 * ny + 0.45 * nz          # light from the upper left
            tone = 3 if lit > 0.62 else (2 if lit > 0.10 else 1)
            if (x - SEG_OX) % SEG_W == 0 or (y - SEG_OY) % SEG_H == 0:
                tone -= 1                                      # grid lines are one step darker
            if y <= TOP_ROWS:
                tone = 0                                       # darker top
            elif y == TOP_ROWS + 1:
                tone = min(tone, 1)
            c.set(x, y, shade[max(0, tone)])


def lever(c, pts):
    for i, (x, y) in enumerate(pts):
        c.set(x - 1, y, WHITE if i in (3, 4) else GREY)
        c.set(x, y, DARK_GREY if i > 2 else GREY)


def build_fill(pin=True, lifted=False):
    """Un-outlined grenade on the FILL_W x FILL_H grid."""
    c = C(FILL_W, FILL_H)
    body(c)
    # neck (darker top continues up into the fuse head)
    c.rect(4, 3, 5, 1, OLIVE_DEEP)
    c.rect(3, 4, 7, 1, OLIVE_DEEP)
    metal_cap(c)
    lever(c, LEVER_LIFTED if lifted else LEVER_REST)
    if pin:
        for x, y, col in RING:
            c.set(x, y + 1, col)                  # ring sits one row lower (y 1..4)
        for x in range(4, 8):
            c.set(x, 3, GREY)                     # shaft through the neck
        c.set(8, 3, DARK_GREY)
    return c


def finish(fill, w, h, ox=1, oy=1):
    c = C(w, h)
    c.paste(fill, ox, oy)
    c.outline()
    return c


def pin_sprite():
    """Pin + ring alone (6 x 4 fill -> 8 x 6 logical -> 32 x 24 px)."""
    f = C(6, 4)
    for x, y, col in RING:
        f.set(x, y, col)
    f.set(4, 2, GREY)
    f.set(5, 2, DARK_GREY)
    return finish(f, 8, 6)


# ----------------------------------------------------------------------------
# SPIN - the grenade is NOT rotated as an image. For every spin frame each
# destination pixel is mapped back (by the frame's angle) to a spot on the
# un-outlined grenade grid and takes the palette color found there (majority of
# 3 x 3 sample points per pixel, so thin parts survive). Then the outline is drawn
# fresh around the result. All frames share the pivot (the body centre).
# ----------------------------------------------------------------------------
def spin_frame(k):
    src = build_fill(pin=SPIN_WITH_PIN, lifted=not SPIN_WITH_PIN)
    ang = 2 * math.pi * k / SPIN_FRAMES
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = BODY_CX, BODY_CY                       # pivot in the source
    dcx, dcy = SPIN_W // 2 + .5, SPIN_H // 2 + .5   # pivot in the destination (a pixel centre)
    offs = (-1 / 3, 0.0, 1 / 3)
    dst = C(SPIN_W, SPIN_H)
    for Y in range(SPIN_H):
        for X in range(SPIN_W):
            votes = {}
            order = []
            for oy in offs:
                for ox in offs:
                    dx, dy = X + .5 + ox - dcx, Y + .5 + oy - dcy
                    sx = px + ca * dx + sa * dy
                    sy = py - sa * dx + ca * dy
                    v = src.get(math.floor(sx), math.floor(sy))
                    votes[v] = votes.get(v, 0) + 1
                    if v not in order:
                        order.append(v)
            best = max(order, key=lambda v: (votes[v], -order.index(v)))
            dst.g[Y][X] = best
    dst.outline()
    return dst


# ----------------------------------------------------------------------------
# EXPLOSION - built from flat colored "lumpy discs" made of blocks.
# The grid is EXPL_PX / (S * EXPL_BLOCK) blocks wide (24 by default); every block
# is EXPL_BLOCK x EXPL_BLOCK logical pixels.
# ----------------------------------------------------------------------------
LUMP_VAR = [0.0, 0.6, -0.4, 0.9, -0.7, 0.3, -0.2]   # per-lump size/offset variation: edit for a
LUMPS = len(LUMP_VAR)                                # different cloud silhouette
# Flying sparks: (angle deg, distance at frame 4, speed/frame, rise/frame, last visible frame)
EMBERS = [(20, 8.0, .5, .5, 7), (75, 7.0, .4, .7, 7), (130, 8.5, .5, .5, 6),
          (200, 7.5, .6, .4, 7), (250, 8.0, .4, .6, 5), (310, 7.0, .5, .5, 6),
          (165, 5.5, .6, .8, 7), (350, 9.0, .3, .3, 5)]
EMBER_COLORS = [YELLOW, ORANGE, RED, DARK_RED]
# Smoke puffs of frame 6 (dx, dy from centre, radius in blocks)
PUFFS = [(-4, -1, 3.2), (3.5, -2.5, 3.0), (0, 3.5, 2.4), (-1, -5, 2.2)]


def disk(c, cx, cy, r, col):
    for y in range(c.h):
        for x in range(c.w):
            if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r:
                c.set(x, y, col)


def blob(c, cx, cy, R, col, phase=0.0):
    """Lumpy cloud: a core disc plus LUMPS smaller discs around it."""
    disk(c, cx, cy, R * 0.70, col)
    for i, v in enumerate(LUMP_VAR):
        a = phase + i * 2 * math.pi / LUMPS
        d = R * 0.42 * (1 + 0.2 * v)
        disk(c, cx + math.cos(a) * d, cy + math.sin(a) * d, R * 0.34 * (1 + 0.1 * v), col)


def explosion_frame(f):
    n = EXPL_PX // (S * EXPL_BLOCK)
    c = C(n, n)
    m = n / 2
    if f == 0:      # small white-yellow flash
        blob(c, m, m, 3.4, YELLOW, 0.0)
        disk(c, m, m, 2.0, WHITE)
    elif f == 1:    # fireball grows
        blob(c, m, m, 8.0, DARK_RED, 0.0)
        blob(c, m, m, 6.8, ORANGE, 0.5)
        blob(c, m, m, 4.5, YELLOW, 1.0)
        blob(c, m, m, 2.5, WHITE, 0.2)
    elif f == 2:    # big fireball, smoke starts behind it
        blob(c, m, m, 11.0, DARK_GREY, 0.9)
        blob(c, m, m, 10.2, DARK_RED, 0.0)
        blob(c, m, m, 8.9, RED, 0.4)
        blob(c, m, m, 6.6, ORANGE, 0.8)
        blob(c, m, m, 4.0, YELLOW, 0.3)
    elif f == 3:    # peak: ring of dark smoke around the fire
        blob(c, m, m, 11.6, DARK_GREY, 0.3)
        blob(c, m, m, 9.2, DARK_RED, 1.1)
        blob(c, m, m, 8.0, RED, 0.2)
        blob(c, m, m, 5.4, ORANGE, 0.7)
        blob(c, m, m, 2.6, YELLOW, 0.1)
    elif f == 4:    # shrinks, turns into grey smoke
        blob(c, m, m - .5, 11.0, DARK_GREY, 0.6)
        blob(c, m, m - .5, 10.0, GREY, 0.1)
        blob(c, m, m, 6.0, DARK_RED, 0.9)
        blob(c, m, m, 4.8, RED, 0.3)
        blob(c, m, m, 2.6, ORANGE, 0.0)
    elif f == 5:    # smoke cloud with a last hot spot, starting to rip open
        blob(c, m, m - 1, 9.4, DARK_GREY, 0.2)
        blob(c, m, m - 1, 8.4, GREY, 0.8)
        blob(c, m + 1, m - 1, 4.5, DARK_GREY, 0.4)      # darker patch
        blob(c, m + 1, m - 1, 3.4, GREY, 0.0)
        disk(c, m - 1, m, 1.6, ORANGE)
        for hx, hy, hr in ((m - 4, m - 4, 1.4), (m + 4, m, 1.4), (m - 1, m + 4, 1.2)):
            disk(c, hx, hy, hr, 0)                         # holes
    elif f == 6:    # smoke breaks into puffs
        for dx, dy, r in PUFFS:
            blob(c, m + dx, m - 1 + dy, r + 0.9, DARK_GREY, dx)
        for dx, dy, r in PUFFS:
            blob(c, m + dx, m - 1 + dy, r, GREY, dx)
    else:           # f == 7: only a tiny wisp and embers remain
        blob(c, m - 1, m - 4, 1.9, DARK_GREY, 0.0)
        disk(c, m - 1, m - 4, 0.9, GREY)
    if f >= 4:      # embers fly out
        for i, (ang, d4, spd, rise, last) in enumerate(EMBERS):
            if f > last:
                continue
            d = d4 + spd * (f - 4)
            x = m + math.cos(math.radians(ang)) * d
            y = m - math.sin(math.radians(ang)) * d - rise * (f - 4)
            col = EMBER_COLORS[min(3, (f - 4) + (i % 2))]
            c.set(int(x), int(y), col)
    return c


# ----------------------------------------------------------------------------
# PREVIEW - everything on a dark and on a light background
# ----------------------------------------------------------------------------
def preview(still, spins, expls):
    font = ImageFont.load_default()
    pad = 10
    half = [im.resize((im.width // 2, im.height // 2), Image.NEAREST) for im in expls]
    cols = max(len(spins), len(half))
    width = pad + cols * (spins[0].width + pad)
    rows = [still, spins, half]
    labels = ["grenade / grenade_nopin / grenade_pin", "grenade_spin0-%d" % (len(spins) - 1),
              "explosion0-%d (shown at half size)" % (len(expls) - 1)]
    rh = [max(i.height for i in r) + 22 for r in rows]
    ph = sum(rh) + pad
    out = Image.new("RGBA", (width, ph * 2), (0, 0, 0, 255))
    for p, (bg, fg) in enumerate((((22, 24, 44, 255), (230, 230, 245, 255)),
                                  ((226, 232, 240, 255), (30, 30, 44, 255)))):
        d = ImageDraw.Draw(out)
        d.rectangle([0, p * ph, width, (p + 1) * ph], fill=bg)
        y = p * ph + pad // 2
        for r, lab, h in zip(rows, labels, rh):
            d.text((pad, y), lab, fill=fg, font=font)
            x = pad
            for im in r:
                out.alpha_composite(im, (x, y + 14))
                x += im.width + pad
            y += h
    return out.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    rest = finish(build_fill(True, False), GREN_W, GREN_H).image()
    nopin = finish(build_fill(False, True), GREN_W, GREN_H).image()
    pin = pin_sprite().image()
    rest.save(os.path.join(OUT, "grenade.png"))
    nopin.save(os.path.join(OUT, "grenade_nopin.png"))
    pin.save(os.path.join(OUT, "grenade_pin.png"))
    spins = []
    for k in range(SPIN_FRAMES):
        im = spin_frame(k).image()
        im.save(os.path.join(OUT, "grenade_spin%d.png" % k))
        spins.append(im)
    expls = []
    for f in range(EXPL_FRAMES):
        cv = explosion_frame(f)
        im = cv.image(EXPL_PX // cv.w)
        im.save(os.path.join(OUT, "explosion%d.png" % f))
        expls.append(im)
    preview([rest, nopin, pin], spins, expls).save(os.path.join(OUT, "grenade_preview.png"))
    print("wrote %d files to %s" % (3 + SPIN_FRAMES + EXPL_FRAMES + 1, OUT))


if __name__ == "__main__":
    main()
