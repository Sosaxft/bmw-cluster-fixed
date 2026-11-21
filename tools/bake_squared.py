#!/usr/bin/env python3
"""Bake the Live Cockpit Map theme's lettering for Cluster Themes (apps/cluster_themes/hud/fonts/), Redline's HUD
lettering (the G80 M3 / M4 look):

  - q_*  squared digits, the G80 M3 / M4 HUD's look as Redline draws them (redline/hud-m.js sqGlyph: 7-segment
         strokes joined at the corners, 1.15 x as wide as tall, the stroke a quarter of the height, plus P R N D S M),
         drawn here 4x and scaled down, in bake_fonts.py's atlas format;
  - u_*  Ubuntu (Bold / Medium, Ubuntu Font Licence 1.0, tools/fonts-src/Ubuntu-UFL.txt), Redline's own text font.

    python3 tools/bake_squared.py           (needs Pillow)
"""
import base64, json, os
from PIL import Image, ImageDraw

import bake_fonts as B

OUT = os.path.join(B.APPS, 'cluster_themes', 'hud', 'fonts')
SS = 4                     # supersampling
GAP = 0.22                 # letter spacing, x the height (sqText)
SQ = {'0': 'abcdef', '2': 'abged', '3': 'abgcd', '4': 'g', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg',
      '9': 'abfgcd', '-': 'g', 'S': 'afgcd', 'P': 'abfge', 'N': 'efbc', 'R': 'abfge', 'M': 'efabc', 'D': 'abcdef'}


def adv_w(ch, h):
    return sq_t(h) if ch == '.' else h * 0.55 if ch == '1' else h * 1.15


def sq_t(h):
    return max(1.9, h * 0.25)


def glyph(d, ch, x, y, h):
    """sqGlyph, on a PIL draw at (x, y), h tall."""
    w, t, hh = adv_w(ch, h), sq_t(h), h / 2
    rect = lambda r: d.rectangle([r[0], r[1], r[0] + r[2] - 1, r[1] + r[3] - 1], fill=255)
    quad = lambda pts: d.polygon([tuple(p) for p in pts], fill=255)
    if ch == '.':
        rect([x, y + h - t, t, t]); return
    if ch == '1':
        rect([x + w - t, y, t, h]); rect([x + w * 0.15, y, w * 0.85, t]); return
    R = {'a': [x, y, w, t], 'g': [x, y + hh - t / 2, w, t], 'd': [x, y + h - t, w, t],
         'f': [x, y, t, hh + t / 2], 'b': [x + w - t, y, t, hh + t / 2], 'e': [x, y + hh - t / 2, t, hh + t / 2],
         'c': [x + w - t, y + hh - t / 2, t, hh + t / 2]}
    if ch == 'D':
        R['a'] = [x, y, w - t, t]; R['d'] = [x, y + h - t, w - t, t]; R['b'] = [x + w - t, y + t, t, hh]
        R['c'] = [x + w - t, y + hh - t / 2, t, hh - t / 2]
    for k in SQ[ch]:
        rect(R[k])
    if ch == 'D':
        quad([[x + w - t, y], [x + w, y + t], [x + w - t, y + t]]); quad([[x + w - t, y + h - t], [x + w, y + h - t], [x + w - t, y + h]])
    diag = lambda x0, y0, x1, y1: quad([[x0, y0], [x0 + t * 1.1, y0], [x1, y1], [x1 - t * 1.1, y1]])
    if ch == 'N': diag(x + t * 0.4, y, x + w - t * 0.4, y + h)
    if ch == 'R': diag(x + w * 0.35, y + hh, x + w + t * 0.45, y + h)
    if ch == 'M': rect([x + w / 2 - t / 2, y, t, hh])
    if ch == '4':
        sx = x + w * 0.8 - t
        rect([sx, y, t, h])
        quad([[sx - t * 0.9, y], [sx + t * 0.6, y], [x + t * 1.6, y + hh - t / 2], [x, y + hh - t / 2]])


def bake_sq(name, h, chars):
    P = B.PAD
    height = h + 2 * P
    cells = []
    for c in chars:
        adv = round(adv_w(c, h) + GAP * h) if c != ' ' else round(h * 0.6)
        if c == ' ':
            cells.append((c, None, 0, adv)); continue
        w = int(adv_w(c, h) + 0.999) + 2 * P + 2     # the R's leg reaches a little past its box
        big = Image.new('L', (w * SS, height * SS), 0)
        glyph(ImageDraw.Draw(big), c, P * SS, P * SS, h * SS)
        cells.append((c, big.resize((w, height), Image.LANCZOS), -P, adv))
    x = y = 0
    placed = {}
    for c, img, ox, adv in cells:
        if img is None: continue
        if x + img.width > B.ATLAS_W: x, y = 0, y + height
        placed[c] = (x, y); x += img.width
    atlas_h = y + height
    atlas = Image.new('L', (B.ATLAS_W, atlas_h), 0)
    glyphs = {}
    for c, img, ox, adv in cells:
        if img is None:
            glyphs[c] = {'x': 0, 'y': 0, 'w': 0, 'h': 0, 'ox': 0, 'advance': adv}; continue
        gx, gy = placed[c]
        atlas.paste(img, (gx, gy))
        glyphs[c] = {'x': gx, 'y': gy, 'w': img.width, 'h': img.height, 'ox': ox, 'advance': adv}
    meta = {'source': 'squared (Redline hud-m.js sqGlyph)', 'size': h, 'cellHeight': height, 'baseline': P + h,
            'glyphs': glyphs, 'width': B.ATLAS_W, 'height': atlas_h, 'alpha': base64.b64encode(atlas.tobytes()).decode('ascii')}
    with open(os.path.join(OUT, name + '.json'), 'w') as f:
        json.dump(meta, f, separators=(',', ':'))
    print('%-8s %3dpx  cell %3d  atlas %dx%d' % (name, h, height, B.ATLAS_W, atlas_h))


DIG = '0123456789'
SQUARED = [
    ('q_big', 60, DIG + 'PRNDSM-'),       # the speed and the gear
    ('q_scale', 21, DIG),                 # the scale numbers
]
UBUNTU = [
    ('u_small', 'Ubuntu-Medium.ttf', 25, B.DIGITS + '/.:-°% '),               # the gauges' numbers (1/2, temperatures)
    ('u_cap', 'Ubuntu-Medium.ttf', 22, B.UPPER + B.LOWER + B.DIGITS + '/.:-°%x '),   # mph, 1/min x 1000, units, the badge
    ('u_val', 'Ubuntu-Bold.ttf', 28, B.DIGITS + ':.-+° '),                    # the strip's clock, range, outside
]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for spec in SQUARED:
        bake_sq(*spec)
    for name, file, size, chars in UBUNTU:
        B.bake(OUT, name, file, size, chars)
