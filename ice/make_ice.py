#!/usr/bin/env python3
"""
Ice block that is drawn on top of a frozen zombie, plus crack stages, shards
and a preview sheet.

Run:   python3 make_ice.py [output_dir]
Needs: pip install pillow numpy
Output (default ./ice/):
    ice_block.png                    the block, interior see-through (INTERIOR_ALPHA)
    ice_clear.png                    fully transparent interior (outline, rim, highlights only)
    ice_crack0.png .. ice_crack2.png progressively more cracks ("about to shatter")
    ice_shard0.png .. ice_shard5.png six separate pieces, each <= 48x48
    ice_preview.png                  contact sheet on a dark and a light background
                                     (a crude coloured stand-in sits behind the blocks
                                     so you can judge the transparency; it is NOT part
                                     of the sprites)

Same method as the zombie scripts: everything is drawn on a grid of "logical
pixels" using palette indices and scaled S times with nearest-neighbour, so
every sprite pixel is a crisp S x S block. Nothing is anti-aliased and there
are no gradients or soft shadows.

ALPHA RULE (the only alpha values that ever appear are 0, INTERIOR_ALPHA, 255)
  * "fill" pixels (the water-clear inside of the block, shards and puddle)
    get INTERIOR_ALPHA;
  * outline, rim, highlights, glints, bubbles and cracks are fully opaque (255);
  * everything outside the shape is 0.
  Change INTERIOR_ALPHA below to make the ice more or less see-through.

Where to change things
  * BLOCK_W, BLOCK_H, S                  size of the block (logical px) / pixel scale.
                                         46 x 56 at S = 4 gives 184 x 224. Every
                                         position below is a FRACTION of the block, so a
                                         smaller block just works.
  * INTERIOR_ALPHA                       transparency of the fill (0-255)
  * PAL                                  the 7-colour palette (index -> RGB)
  * CORNER, NOTCHES, TOP_CHIPS, BOTTOM_CHIPS, PUDDLE_H   the block's shape
  * RIM_TOP / RIM_SIDE / RIM_BOTTOM, RIM_TONES            frosted rim thickness / colours
  * STREAKS, SPARKLES, GLINTS, BUBBLES                    highlights and bubbles
  * CRACKS                               crack patterns, one list per level
  * SHARD_POLYS                          the six shard outlines (12 x 12 grid)
  * CLEAR_KEEPS_DETAILS                  put bubbles/cracks into ice_clear.png too
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------- settings
S = 4                       # pixel scale (logical px -> real px)
BLOCK_W, BLOCK_H = 46, 56   # block size in logical px (x S = 184 x 224)
INTERIOR_ALPHA = 90         # 0-255: alpha of every "fill" pixel. The ONLY partial alpha.
CLEAR_KEEPS_DETAILS = False  # True: ice_clear.png also keeps bubbles and cracks
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ice")

# 7 colours (index -> RGB). Edit these to recolour the ice.
OUTLINE, ICE_DARK, ICE_MID, ICE_LIGHT, WHITE, CYAN, CRACK = 1, 2, 3, 4, 5, 6, 7
PAL = {
    OUTLINE: (16, 32, 82),      # deep blue outline
    ICE_DARK: (48, 104, 184),   # icy blue, dark
    ICE_MID: (104, 168, 228),   # icy blue, mid
    ICE_LIGHT: (172, 220, 248), # icy blue, light
    WHITE: (244, 250, 255),     # highlights / frost
    CYAN: (92, 224, 238),       # little cyan accents
    CRACK: (26, 62, 138),       # cracks
}
FILL_A, FILL_B = ICE_LIGHT, ICE_MID   # interior tones (both use INTERIOR_ALPHA)

# ---- block shape ---------------------------------------------------------
CORNER = 4                  # roundness of the chunky corners (logical px)
PUDDLE_H = 4                # rows at the bottom used by the puddle under the block
# Side notches that make the block irregular: (side 'L'/'R', from_y, to_y, depth_px)
# y values are fractions of the block body's height.
NOTCHES = [("L", 0.30, 0.36, 1), ("R", 0.55, 0.64, 1), ("R", 0.15, 0.19, 1),
           ("L", 0.80, 0.86, 1)]
# Chips taken out of the top / bottom edge: (from_x, to_x, depth_px), x as fraction of width
TOP_CHIPS = [(0.55, 0.68, 1), (0.12, 0.20, 1), (0.82, 1.00, 2)]
BOTTOM_CHIPS = [(0.40, 0.50, 1)]

# ---- frosted rim (thicker on top and sides) -----------------------------
RIM_TOP, RIM_SIDE, RIM_BOTTOM = 4, 3, 2      # rim thickness inside the outline
# Colour per rim row, counted from the outline inwards. An entry is either a
# palette index or a pair (a, b) drawn as a checkerboard (hard-edged "frost").
RIM_TONES = {
    "top":    [ICE_LIGHT, (WHITE, ICE_LIGHT), ICE_LIGHT, (ICE_MID, ICE_LIGHT)],   # lit side
    "left":   [ICE_LIGHT, (WHITE, ICE_LIGHT), (ICE_MID, ICE_LIGHT)],
    "right":  [ICE_DARK, (ICE_DARK, ICE_MID), ICE_MID],                           # shaded side
    "bottom": [WHITE, (WHITE, ICE_LIGHT)],                                        # frost line
}

# ---- highlights (positions are fractions of the block) -------------------
# Long white streaks along the rim: (side, from, to, rim_row) - from/to are
# fractions along that side (x for top/bottom, y for left/right).
STREAKS = [("top", 0.10, 0.46, 2), ("top", 0.52, 0.60, 3), ("left", 0.08, 0.38, 2)]
SPARKLES = [(0.13, 0.09)]            # little "+" glints, (fx, fy)
# Diagonal glints inside: (fx, fy, length, colour); they run from the upper right to the lower left
GLINTS = [(0.20, 0.22, 6, WHITE), (0.28, 0.15, 3, WHITE), (0.74, 0.58, 5, CYAN),
          (0.80, 0.50, 3, CYAN), (0.30, 0.70, 4, WHITE)]
# Air bubbles: (fx, fy, size 1-3)
BUBBLES = [(0.30, 0.40, 3), (0.62, 0.30, 2), (0.70, 0.70, 3), (0.35, 0.76, 2),
           (0.55, 0.60, 1), (0.22, 0.52, 1)]

# ---- cracks: polylines of (fx, fy) points. Level n draws levels 0..n --------
# ice_block.png = level 0, ice_crack0/1/2.png = levels 1, 2, 3.
CRACKS = {
    0: [[(0.55, 0.35), (0.50, 0.40), (0.52, 0.46)],
        [(0.30, 0.60), (0.34, 0.64), (0.33, 0.70)],
        [(0.68, 0.72), (0.64, 0.76)]],
    1: [[(0.62, 0.08), (0.58, 0.20), (0.62, 0.32), (0.55, 0.45), (0.58, 0.55)],
        [(0.58, 0.20), (0.48, 0.26)]],
    2: [[(0.06, 0.45), (0.20, 0.48), (0.30, 0.55), (0.42, 0.52), (0.55, 0.58)],
        [(0.30, 0.55), (0.28, 0.68), (0.22, 0.78)],
        [(0.45, 0.90), (0.48, 0.78), (0.44, 0.66)]],
    3: [[(0.70, 0.30), (0.85, 0.38), (0.94, 0.34)],
        [(0.58, 0.55), (0.72, 0.62), (0.80, 0.78)],
        [(0.15, 0.15), (0.25, 0.28), (0.22, 0.40)],
        [(0.35, 0.20), (0.45, 0.12), (0.50, 0.05)],
        [(0.80, 0.78), (0.90, 0.88)]],
}

# ---- shards: polygons on a 12 x 12 grid (vertices in logical px) ------------
SHARD_POLYS = [
    [(1, 10), (5, 0), (11, 8)],
    [(0, 3), (8, 0), (11, 6), (4, 11)],
    [(0, 0), (8, 2), (3, 8)],
    [(2, 1), (9, 1), (11, 6), (6, 10), (1, 7)],
    [(0, 6), (10, 0), (11, 3), (3, 9)],
    [(1, 2), (6, 0), (9, 4), (7, 9), (2, 8)],
]
SHARD_RIM = 1                        # rim thickness of the shards (they are tiny: 1 keeps an interior)


# ------------------------------------------------------------------ canvas
class C:
    """Tiny indexed-colour pixel canvas (0 = empty). Every pixel also carries a
    'fill' flag: fill pixels are drawn with INTERIOR_ALPHA, all others with 255."""

    def __init__(s, w, h):
        s.w, s.h = w, h
        s.g = [[0] * w for _ in range(h)]
        s.f = [[False] * w for _ in range(h)]

    def set(s, x, y, c, fill=False):
        if 0 <= x < s.w and 0 <= y < s.h:
            s.g[y][x] = c
            s.f[y][x] = fill

    def crop(s):
        ys = [y for y in range(s.h) if any(s.g[y])]
        xs = [x for x in range(s.w) if any(s.g[y][x] for y in range(s.h))]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        o = C(x1 - x0 + 1, y1 - y0 + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                o.g[y - y0][x - x0] = s.g[y][x]
                o.f[y - y0][x - x0] = s.f[y][x]
        return o

    def image(s):
        a = np.zeros((s.h, s.w, 4), dtype=np.uint8)
        for y in range(s.h):
            for x in range(s.w):
                v = s.g[y][x]
                if v:
                    a[y, x] = (*PAL[v], INTERIOR_ALPHA if s.f[y][x] else 255)
        return Image.fromarray(a, "RGBA").resize((s.w * S, s.h * S), Image.NEAREST)


# ------------------------------------------------------------ small helpers
def line(x0, y0, x1, y1):
    """Bresenham line, list of (x, y)."""
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return pts
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def hash2(x, y):
    return (x * 73856093 ^ y * 19349663) % 1000


# ----------------------------------------------------------------- the shape
def block_mask(w, h):
    """True where the block's body is. Rounded chunky corners, side notches and
    chipped top/bottom edges; the puddle rows are left empty."""
    body_h = h - PUDDLE_H + 1
    m = [[False] * w for _ in range(h)]

    def corner_inset(d):
        if d >= CORNER:
            return 0
        return CORNER - int(math.sqrt(max(0, CORNER * CORNER - (CORNER - d) ** 2)))

    for y in range(body_h):
        inset = max(corner_inset(y), corner_inset(body_h - 1 - y))
        left, right = inset, w - 1 - inset
        for side, f0, f1, depth in NOTCHES:
            if int(f0 * body_h) <= y <= int(f1 * body_h):
                if side == "L":
                    left += depth
                else:
                    right -= depth
        for x in range(left, right + 1):
            m[y][x] = True
    for f0, f1, depth in TOP_CHIPS:
        for x in range(int(f0 * w), min(w, int(f1 * w) + 1)):
            col = [y for y in range(h) if m[y][x]]
            for y in col[:depth]:
                m[y][x] = False
    for f0, f1, depth in BOTTOM_CHIPS:
        for x in range(int(f0 * w), min(w, int(f1 * w) + 1)):
            col = [y for y in range(h) if m[y][x]]
            for y in col[len(col) - depth:]:
                m[y][x] = False
    return m


def ice_body(c, mask, thick, clear=False):
    """Draw outline, frosted rim and see-through fill for `mask` onto canvas c.
    thick = (top, side, side, bottom) rim thickness. Returns a dict
    (x, y) -> (kind, side, depth) used by the highlight / crack passes."""
    h, w = len(mask), len(mask[0])

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y][x]

    top, bot, left, right = {}, {}, {}, {}
    for x in range(w):
        ys = [y for y in range(h) if mask[y][x]]
        if ys:
            top[x], bot[x] = ys[0], ys[-1]
    for y in range(h):
        xs = [x for x in range(w) if mask[y][x]]
        if xs:
            left[y], right[y] = xs[0], xs[-1]
    info = {}
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            if not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.set(x, y, OUTLINE)
                info[(x, y)] = ("outline", None, 0)
                continue
            cand = [("top", y - top[x], thick[0]), ("left", x - left[y], thick[1]),
                    ("right", right[y] - x, thick[2]), ("bottom", bot[x] - y, thick[3])]
            cand = [t for t in cand if t[1] <= t[2]]
            if cand:
                side, d, _ = min(cand, key=lambda t: t[1])
                tones = RIM_TONES[side]
                tone = tones[min(d - 1, len(tones) - 1)]
                if isinstance(tone, tuple):
                    tone = tone[(x + y) % 2]
                if d >= 2 and hash2(x, y) % 13 == 0:
                    tone = WHITE                      # frost speckle
                c.set(x, y, tone)
                info[(x, y)] = ("rim", side, d)
            else:
                t = x / w + y / h                      # hard-edged tone bands
                tone = FILL_B if (t > 1.30 or (t > 1.22 and (x + y) % 2 == 0)) else FILL_A
                if not clear:
                    c.set(x, y, tone, fill=True)
                info[(x, y)] = ("fill", None, 0)
    return info


# ----------------------------------------------------------- decoration passes
def streaks(c, info, w, h, items):
    for side, f0, f1, depth in items:
        for (x, y), (kind, s, d) in info.items():
            if kind == "rim" and s == side and d == depth:
                t = (x / w) if side in ("top", "bottom") else (y / h)
                if f0 <= t <= f1:
                    c.set(x, y, WHITE)


def sparkle(c, info, x, y):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        if info.get((x + dx, y + dy), ("outline",))[0] != "outline" and (x + dx, y + dy) in info:
            c.set(x + dx, y + dy, WHITE)


def glint(c, info, x, y, length, colour):
    for i in range(length):
        if info.get((x - i, y + i), ("outline",))[0] in ("fill", "rim"):
            c.set(x - i, y + i, colour)


def bubble(c, info, x, y, size):
    pat = {1: [(0, 0, WHITE)],
           2: [(0, 0, WHITE), (1, 0, ICE_MID), (0, 1, ICE_MID), (1, 1, ICE_MID)],
           3: [(1, 0, ICE_MID), (0, 1, WHITE), (2, 1, ICE_MID), (1, 2, ICE_MID)]}[size]
    if all(info.get((x + dx, y + dy), ("",))[0] == "fill" for dx, dy, _ in pat):
        for dx, dy, col in pat:
            c.set(x + dx, y + dy, col)


def crack(c, info, w, h, pts):
    px = [(round(fx * (w - 1)), round(fy * (h - 1))) for fx, fy in pts]
    cells = []
    for a, b in zip(px, px[1:]):
        cells += line(a[0], a[1], b[0], b[1])
    for i, (x, y) in enumerate(cells):
        if info.get((x, y), ("outline",))[0] in ("fill", "rim"):
            c.set(x, y, CRACK)
    for i, (x, y) in enumerate(cells):           # a lit edge beside every 3rd crack pixel
        if i % 3 == 1 and info.get((x - 1, y), ("",))[0] == "fill":
            c.set(x - 1, y, WHITE)


def puddle(c, w, h, clear):
    """Flat ellipse of water under the block (fill alpha) with an opaque
    outline and a cyan shine; the block is drawn over it afterwards."""
    cx, rx = w / 2, w / 2 - 0.5
    yc, ry = h - PUDDLE_H / 2 - 0.5, PUDDLE_H / 2 + 0.5
    pm = [[((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - yc) / ry) ** 2 <= 1 for x in range(w)]
          for y in range(h)]

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and pm[y][x]

    for y in range(h):
        for x in range(w):
            if pm[y][x]:
                edge = not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if edge:
                    c.set(x, y, OUTLINE)
                elif not clear:
                    c.set(x, y, ICE_MID, fill=True)
    for x in range(int(cx) - 9, int(cx) + 10):    # shine dashes on the second-last row
        if (x // 3) % 2 == 0 and inside(x, h - 2) and c.g[h - 2][x] != OUTLINE:
            c.set(x, h - 2, CYAN)


# ------------------------------------------------------------------ the block
def render_block(level, clear=False):
    """level = crack stage 0..3 (0 = just a few hairline cracks)."""
    w, h = BLOCK_W, BLOCK_H
    c = C(w, h)
    puddle(c, w, h, clear)
    info = ice_body(c, block_mask(w, h), (RIM_TOP, RIM_SIDE, RIM_SIDE, RIM_BOTTOM), clear)
    streaks(c, info, w, h, STREAKS)
    for fx, fy in SPARKLES:
        sparkle(c, info, round(fx * w), round(fy * h))
    for fx, fy, length, col in GLINTS:
        glint(c, info, round(fx * w), round(fy * h), length, col)
    for (x, y), (kind, side, d) in info.items():  # cyan glow on the shaded rim
        if kind == "rim" and side == "right" and d == 1 and y % 5 == 0:
            c.set(x, y, CYAN)
    if not clear or CLEAR_KEEPS_DETAILS:
        for fx, fy, size in BUBBLES:
            bubble(c, info, round(fx * w), round(fy * h), size)
        for lv in range(level + 1):
            for pts in CRACKS.get(lv, []):
                crack(c, info, w, h, pts)
    return c


# ------------------------------------------------------------------- shards
def polygon_mask(poly, size=12):
    m = [[False] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            px, py, ins = x + 0.5, y + 0.5, False
            for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
                if (y0 > py) != (y1 > py) and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
                    ins = not ins
            m[y][x] = ins
    return m


def render_shard(i):
    c = C(12, 12)
    mask = polygon_mask(SHARD_POLYS[i])
    info = ice_body(c, mask, (SHARD_RIM,) * 4)
    streaks(c, info, 12, 12, [("top", 0.0, 0.8, SHARD_RIM), ("left", 0.0, 0.8, SHARD_RIM)])
    glint(c, info, 7, 3, 3, WHITE)
    if i in (1, 3, 5):                           # a hairline crack on some pieces
        crack(c, info, 12, 12, [(0.45, 0.35), (0.55, 0.55), (0.45, 0.75)])
    return c.crop()


# ------------------------------------------------------------------- preview
def stand_in():
    """Crude coloured figure, preview only, to judge the transparency."""
    im = Image.new("RGBA", (40 * S, 50 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for box, col in (((14, 8, 25, 19), (110, 160, 90)), ((12, 20, 27, 34), (190, 80, 70)),
                     ((5, 21, 11, 26), (110, 160, 90)), ((28, 21, 34, 26), (110, 160, 90)),
                     ((13, 35, 18, 48), (70, 80, 130)), ((21, 35, 26, 48), (70, 80, 130))):
        d.rectangle([box[0] * S, box[1] * S, (box[2] + 1) * S - 1, (box[3] + 1) * S - 1], fill=col + (255,))
    return im


def preview(blocks, shards):
    bw, bh = BLOCK_W * S, BLOCK_H * S
    pad, label_h, shard_row = 10, 14, 48 + 10
    pw = pad + len(blocks) * (bw + pad)
    ph = pad + bh + label_h + shard_row + pad
    sheet = Image.new("RGBA", (pw, ph * 2), (0, 0, 0, 255))
    font = ImageFont.load_default()
    figure = stand_in()
    for p, bg in enumerate(((14, 26, 64, 255), (214, 232, 246, 255))):
        top = p * ph
        ImageDraw.Draw(sheet).rectangle([0, top, pw, top + ph], fill=bg)
        txt = (230, 240, 255, 255) if p == 0 else (20, 30, 60, 255)
        for i, (name, im) in enumerate(blocks):
            x, y = pad + i * (bw + pad), top + pad
            sheet.alpha_composite(figure, (x + (bw - figure.width) // 2, y + (bh - figure.height) // 2))
            sheet.alpha_composite(im, (x, y))
            ImageDraw.Draw(sheet).text((x, y + bh + 2), name, fill=txt, font=font)
        x = pad
        for im in shards:
            sheet.alpha_composite(im, (x, top + pad + bh + label_h))
            x += im.width + 12
    return sheet


# ---------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    variants = [("ice_block", 0, False), ("ice_clear", 0, True),
                ("ice_crack0", 1, False), ("ice_crack1", 2, False), ("ice_crack2", 3, False)]
    blocks = []
    for name, level, clear in variants:
        im = render_block(level, clear).image()
        im.save(os.path.join(OUT, name + ".png"))
        blocks.append((name, im))
    shards = []
    for i in range(len(SHARD_POLYS)):
        im = render_shard(i).image()
        im.save(os.path.join(OUT, f"ice_shard{i}.png"))
        shards.append(im)
    preview(blocks, shards).save(os.path.join(OUT, "ice_preview.png"))
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
