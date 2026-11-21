"""
gen_hexmap.py - writes apps/cluster_themes/hud/layouts/hexmap.json, the Hex Map cluster theme (shaders.js hexdash).

After BMW's Live Cockpit Sport view with the map in the middle: a hexagon frame (white outer line, a band glowing red to
orange, an orange inner line; speed scale on the left side, revs on the right), the Waze map filling the hexagon, the
speed big outside it on the left with fuel and range under it, the gear big on the right with the drive mode and the
oil temperature under it, boost and coolant under the hexagon, the clock and outside temperature in the bottom strip.

Edit the numbers here and run:   python3 tools/gen_hexmap.py
It refuses to write a layout whose text boxes overlap each other or the frame.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'layouts', 'hexmap.json')

W, H = 1920, 660            # the frame layer (the strip row under it, y 660..720, is BMW's / the strip widgets')
MAP = [416, 120, 1088, 480]  # BMW's map window, where waze-on-cluster draws (mapcal.json): never cut past it

# the left bracket's outer line (the right one is its mirror)
Y_TOP, Y_BEND, Y_BOT = 110, 330, 604
X_BEND, ROUND = 400, 40
X_TOP, X_BOTC = 545, 525     # the hexagon as wide as BMW's map window allows (the map must stay inside it)     # where the outer line meets the top run / the bottom run
BAND, INNER = 40, 59
SCALE = [594, 150]           # y of the 0 mark, y of the top mark
TICKS = [8, 7]               # speed marks (SPEED_SCALE: 9 labels), rpm marks (0..7)
RPM_MAX = 7000
TOP_END = 980                # top / bottom runs reach past the middle so the two halves join
HOLE_INS = 6                 # the map starts this far inside the inner line


def k_for(x_end, y_end):
    dy = y_end - Y_BEND
    return (x_end - X_BEND) / (math.sqrt(dy * dy + ROUND * ROUND) - ROUND)


K_TOP, K_BOT = k_for(X_TOP, Y_TOP), k_for(X_BOTC, Y_BOT)


def outer_x(y):
    dy = y - Y_BEND
    k = K_TOP if dy < 0 else K_BOT
    return X_BEND + k * (math.sqrt(dy * dy + ROUND * ROUND) - ROUND)


def r(v):
    return round(v, 4)


def text(id_, x, y, w, h, tx, font, color, align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': int(round(x)), 'y': int(round(y)), 'w': int(w), 'h': int(h),
         'text': tx, 'font': font, 'color': color, 'align': align}
    d.update(kw)
    return d


widgets = []
widgets.append({
    'id': 'hex', 'type': 'hexdash', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
    'geo': [Y_TOP, Y_BEND, Y_BOT, X_BEND], 'k': [r(K_TOP), r(K_BOT), ROUND], 'band': BAND, 'inner': INNER,
    'scale': SCALE, 'ticks': TICKS, 'rpmMax': RPM_MAX,
    # fuel under the speed (fills to the right), oil temperature under the gear (fills to the left)
    'fuelSeg': [250, 436, 80, 436], 'oilSeg': [1670, 436, 1840, 436],
    'strip': [30, 492, 2, 140], 'topEnd': TOP_END, 'road': [Y_BEND, 1.4],
    'hole': MAP, 'holeWhen': 'mapUp', 'holeRadius': HOLE_INS,
})

# scale numbers just outside the outer line
for i in range(TICKS[0] + 1):
    y = SCALE[0] - i / TICKS[0] * (SCALE[0] - SCALE[1])
    xr = outer_x(y) - 14
    widgets.append(text('spd%d' % i, xr - 80, y - 11, 80, 23, '{{spd:%d}}' % i, 'h_scale', 'hscale', 'right',
                        near=['speed', i], nearColor='horange'))
for i in range(TICKS[1] + 1):
    y = SCALE[0] - i / TICKS[1] * (SCALE[0] - SCALE[1])
    xl = W - outer_x(y) + 14
    widgets.append(text('rpm%d' % i, xl, y - 11, 44, 23, str(i), 'h_scale', 'hscale', 'left',
                        near=['rpm', i], nearColor='horange'))

widgets += [
    text('badge', 810, 72, 300, 26, '{{badge}}', 'h_unit', 'dim'),
    # left: speed, unit, fuel bar (shader) with its icon, range
    text('speed', 40, 288, 240, 68, '{{speed}}', 'h_speed', 'fg'),
    text('speed_unit', 110, 360, 100, 26, '{{u:speedLc}}', 'h_unit', 'dim'),
    {'id': 'fuel_icon', 'type': 'icon', 'icon': 'fuel', 'z': 5, 'x': 42, 'y': 423, 'w': 22, 'h': 26, 'color': 'dim'},
    text('range', 70, 457, 100, 25, '{{range}}', 'h_val', 'fg', 'right'),
    text('range_u', 176, 457, 40, 26, '{{u:distLc}}', 'h_unit', 'dim', 'left'),
    # right: gear (S2 / D3 / P), drive mode, oil bar (shader) with its icon, oil temperature
    text('gear', 1640, 290, 240, 64, '{{gear}}', 'h_gear', 'fg', hotWhen='now'),
    text('mode', 1640, 362, 250, 22, '{{mode}}', 'h_label', 'dim'),
    {'id': 'oil_icon', 'type': 'icon', 'icon': 'oilcan', 'z': 5, 'x': 1850, 'y': 425, 'w': 34, 'h': 22, 'color': 'dim'},
    text('oil', 1690, 457, 100, 25, '{{oil}}', 'h_val', 'fg', 'right'),
    text('oil_unit', 1796, 457, 40, 26, '{{u:temp}}', 'h_unit', 'dim', 'left'),
    {'id': 'mstripe', 'type': 'stripe', 'z': 5, 'x': 1705, 'y': 520, 'w': 120, 'h': 22},
    # under the hexagon (between its bottom line and the warning lights)
    text('boost', 700, 622, 140, 25, '{{boost}}', 'h_val', 'fg', 'right', toggle='showBoost'),
    text('boost_unit', 846, 622, 60, 26, '{{u:boost}}', 'h_unit', 'dim', 'left', toggle='showBoost'),
    {'id': 'therm', 'type': 'icon', 'icon': 'therm', 'z': 5, 'x': 990, 'y': 618, 'w': 24, 'h': 30, 'color': 'dim'},
    text('coolant', 1018, 622, 90, 25, '{{coolant}}', 'h_val', 'fg', 'right'),
    text('coolant_unit', 1114, 622, 50, 26, '{{u:temp}}', 'h_unit', 'dim', 'left'),
    # the bottom strip, as the Sport theme (BMW's gear letter shows in the gap x 1380..1460)
    {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60, 'color': 'bg', 'stripRow': 'l'},
    {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60, 'color': 'bg', 'stripRow': 'r'},
    text('strip_time', 144, 680, 124, 25, '{{time}}', 'h_val', 'fg', 'right', stripRow='l'),
    text('strip_ampm', 274, 679, 35, 26, '{{ampmLc}}', 'h_unit', 'dim', 'left', stripRow='l'),
    text('strip_out', 1676, 680, 80, 25, '{{ambient}}', 'h_val', 'fg', 'right', stripRow='r'),
    text('strip_out_u', 1762, 679, 27, 26, '{{u:temp}}', 'h_unit', 'dim', 'left', stripRow='r'),
]

layout = {
    'schemaVersion': 2,
    'name': 'Hex Map',
    'theme': 'hexdash',
    'mapLive': True,
    '_about': ("After BMW's Live Cockpit Sport view with the map in the middle, generated by tools/gen_hexmap.py (edit that "
               "and regenerate). One hexdash effect layer draws the black backdrop and a hexagon frame of two brackets "
               "(speed left 0..200 mph, revs right 0..7000), each a white outer line, a band lit red to orange up to the "
               "value and an orange inner line, closed by their top and bottom runs. While the Waze map shows inside the "
               "theme ('Show Waze map inside the theme', 'mapUp'), the hexagon's inside is cut see-through over the map, "
               "only within BMW's map window (416,120 1088x480), without a rebuild (mapLive); otherwise a road runs in it. "
               "Speed, fuel and range outside on the left, gear, drive mode and oil temperature on the right, boost and "
               "coolant under the hexagon, the clock and outside temperature in the bottom strip, BMW's gear letter left "
               "uncovered. Widget reference: shared/hud.js header."),
    'widgets': widgets,
}


def boxes_overlap(a, b):
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


def check():
    errs = []
    small = [w for w in widgets if w['type'] in ('text', 'icon', 'stripe')]
    for i, a in enumerate(small):
        for b in small[i + 1:]:
            # the strip row and the boost pair are toggled separately; a pair on different rows never shows together
            if boxes_overlap(a, b):
                errs.append('overlap: %s / %s' % (a['id'], b['id']))
    # nothing of ours outside the frame may reach into the bracket (outer line minus its glow) on its rows
    for w in small:
        if w['y'] >= Y_BOT or w['y'] + w['h'] <= Y_TOP:
            continue
        for yy in range(int(w['y']), int(w['y'] + w['h']) + 1, 3):
            ox = outer_x(min(max(yy, Y_TOP), Y_BOT))
            left_of = w['x'] + w['w'] <= ox - 6
            right_of = w['x'] >= W - ox + 6
            inside = w['x'] >= ox + BAND + 10 and w['x'] + w['w'] <= W - ox - BAND - 10
            if not (left_of or right_of or inside):
                errs.append('%s reaches the frame at y %d (outer line x %.0f / %.0f)' % (w['id'], yy, ox, W - ox))
                break
    # the map cut must stay inside BMW's map window
    for yy in range(Y_TOP + 8 + HOLE_INS, Y_BOT - 8 - HOLE_INS + 1, 4):
        ox = outer_x(yy)
        xi = ox + INNER + HOLE_INS
        if xi < MAP[0] or W - xi > MAP[0] + MAP[2]:
            errs.append('map cut past the window at y %d' % yy)
    if not (MAP[1] <= Y_TOP + 8 + HOLE_INS and Y_BOT - 8 - HOLE_INS <= MAP[1] + MAP[3]):
        errs.append('map cut past the window top / bottom')
    return errs


errs = check()
if errs:
    print('\n'.join(errs))
    sys.exit(1)
with open(OUT, 'w') as f:
    json.dump(layout, f, indent=2)
    f.write('\n')
print('wrote %s: %d widgets; outer line x top %.0f, bend %d, bottom %.0f; map at the bend x %.0f..%.0f'
      % (os.path.relpath(OUT, ROOT), len(widgets), outer_x(Y_TOP), X_BEND, outer_x(Y_BOT),
         X_BEND + INNER + HOLE_INS, W - X_BEND - INNER - HOLE_INS))
