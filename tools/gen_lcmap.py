"""
gen_lcmap.py - writes apps/cluster_themes/hud/layouts/lcmap.json, the Live Cockpit Map cluster theme (shaders.js hexlc).

A copy of BMW's own iDrive 7 Live Cockpit screen with the map up (a straight photo of it, Nov 21 2026): the speed bracket
in blue on the left, the rev bracket in red on the right, the Waze map filling the hexagon between them, the speed and
the gear inside it, the slanted fuel and oil gauges in its lower corners, the clock, range and outside temperature in the
bottom strip. The brackets and the scale numbers take the Sport theme's numbers, traced off a real car's Live Cockpit
(sport.json); the speed, gear, gauges and run lengths come from the photo. Lettering: Inter (closest open font to BMW's).

Edit the numbers here and run:   python3 tools/gen_lcmap.py
It refuses to write a layout whose text boxes or icons overlap.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'layouts', 'lcmap.json')

W, H = 1920, 660
MAP = [416, 120, 1088, 480]          # BMW's map window, where waze-on-cluster draws (mapcal.json)

# the Sport theme's brackets, traced off the car (sport.json)
GEO = [120, 310.7, 604.0, 180]
K = [0.5992, 0.7748, 29.0]
BAND, INNER = 40, 59
SCALE, TICKS, RPM_MAX = [594, 154], [8, 7], 7000
# the photo's map view has them shorter and lower than the Sport view's (sport.json 310,360 448,544)
FUEL_SEG, OIL_SEG = [380, 420, 490, 576], [1540, 420, 1430, 576]
# from the photo: the top runs end at x 660, the bottom runs at x 573 (left; mirrored on the right)
TOP_END, BOTTOM_END = 660, 573
# the Sport theme's traced scale numbers (x, y): speed right-aligned in 110 px, revs left-aligned in 60 px
SPD = [(248, 580), (206, 526), (164, 470), (122, 416), (81, 360), (51, 306), (66, 250), (96, 196), (128, 140)]
RPM = [(1562, 580), (1610, 518), (1658, 455), (1706, 392), (1749, 329), (1752, 266), (1719, 203), (1682, 140)]


def text(id_, x, y, w, h, tx, font, color, align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': x, 'y': y, 'w': w, 'h': h, 'text': tx, 'font': font, 'color': color,
         'align': align}
    d.update(kw)
    return d


def icon(id_, name, x, y, w, h, color='dim'):
    return {'id': id_, 'type': 'icon', 'icon': name, 'z': 5, 'x': x, 'y': y, 'w': w, 'h': h, 'color': color}


widgets = [{
    'id': 'lc', 'type': 'hexlc', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
    'geo': GEO, 'k': K, 'band': BAND, 'inner': INNER, 'scale': SCALE, 'ticks': TICKS, 'rpmMax': RPM_MAX,
    'fuelSeg': FUEL_SEG, 'oilSeg': OIL_SEG, 'strip': [BOTTOM_END, 0, 0, 0], 'topEnd': TOP_END,
    'hole': MAP, 'holeWhen': 'mapUp', 'holeRadius': 6,
}]
for i, (x, y) in enumerate(SPD):
    widgets.append(text('spd%d' % i, x, y + 1, 110, 26, '{{spd:%d}}' % i, 'l_scale', 'lscale', 'right',
                        near=['speed', i], nearColor='fg'))
for i, (x, y) in enumerate(RPM):
    widgets.append(text('rpm%d' % i, x, y + 1, 60, 26, str(i), 'l_scale', 'lscale', 'left', near=['rpm', i], nearColor='fg'))
widgets += [
    text('mph_cap', 338, 88, 80, 25, '{{u:speedLc}}', 'l_unit', 'lblue'),
    text('rpm_cap', 1442, 88, 200, 25, '1/min x 1000', 'l_unit', 'lred'),
    text('badge', 810, 72, 300, 25, '{{badge}}', 'l_unit', 'dim'),
    # inside the hexagon: the speed on the left, the gear on the right (the photo)
    text('speed', 395, 300, 220, 71, '{{speed}}', 'l_big', 'fg'),
    text('speed_unit', 455, 374, 100, 25, '{{u:speedLc}}', 'l_unit', 'dim'),
    text('gear', 1380, 300, 220, 71, '{{gear}}', 'l_big', 'fg', hotWhen='now'),
    # the fuel and oil gauges' ends and icons (the Sport theme's, kept up with the map as on BMW's screen)
    # the fuel and oil gauges: thick slanted bars (shader), three numbers along each and the icon (as the photo)
    text('f_full', 393, 407, 60, 26, '1', 'l_scale', 'fg'),
    text('f_half', 448, 485, 60, 26, '1/2', 'l_scale', 'fg'),
    icon('fuel_icon', 'fuel', 512, 485, 22, 26),
    text('f_empty', 503, 563, 60, 26, '0', 'l_scale', 'fg'),
    text('o_hot', 1467, 407, 60, 26, '{{temp:150}}', 'l_scale', 'fg'),
    text('o_mid', 1412, 485, 60, 26, '{{temp:100}}', 'l_scale', 'fg'),
    icon('oil_icon', 'oilcan', 1370, 522, 34, 22, 'lblue'),
    text('o_cold', 1357, 563, 60, 26, '{{temp:50}}', 'l_scale', 'fg'),
    # the bottom strip, as the Sport theme (BMW's gear letter shows in the gap x 1380..1460)
    {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60, 'color': 'bg', 'stripRow': 'l'},
    {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60, 'color': 'bg', 'stripRow': 'r'},
    text('strip_time', 120, 680, 124, 25, '{{time}}', 'l_val', 'fg', 'right', stripRow='l'),
    text('strip_ampm', 250, 680, 35, 25, '{{ampmLc}}', 'l_unit', 'dim', 'left', stripRow='l'),
    # range bottom-left as in the photo, clear of BMW's seat-belt light (x 587..626)
    text('strip_range', 330, 680, 130, 25, '{{range}}', 'l_val', 'fg', 'right', stripRow='l'),
    text('strip_range_u', 466, 680, 36, 25, '{{u:distLc}}', 'l_unit', 'dim', 'left', stripRow='l'),
    text('strip_out', 1676, 680, 80, 25, '{{ambient}}', 'l_val', 'fg', 'right', stripRow='r'),
    text('strip_out_u', 1762, 680, 27, 25, '{{u:temp}}', 'l_unit', 'dim', 'left', stripRow='r'),
]

layout = {
    'schemaVersion': 2,
    'name': 'Live Cockpit Map',
    'theme': 'lcmap',
    'mapLive': True,
    '_about': ("A copy of BMW's own iDrive 7 Live Cockpit screen with the map up, generated by tools/gen_lcmap.py (edit that "
               "and regenerate). One hexlc effect layer draws the black backdrop, the blue speed bracket (0..200 mph) and the "
               "red rev bracket (0..7000), each a bold outer line, a band shaded inwards and lit to the value and an inner "
               "line, with their top and bottom runs, and the slanted fuel and oil gauges in the lower corners. While the "
               "map shows inside the theme ('mapUp': Maps on cluster, CarPlay's Apple Maps / Waze / Google Maps) the hexagon's "
               "inside is cut see-through over it, only within BMW's map window (416,120 1088x480), without a rebuild "
               "(mapLive); otherwise it stays a dark night-map blue. Each bracket's colour glows in over the map's edges. The "
               "brackets, scale numbers and gauges are the Sport theme's, traced off a real car; the speed and gear sit "
               "inside the hexagon as in the photo; the clock, range and outside temperature in the bottom strip, BMW's "
               "gear letter left uncovered. Widget reference: shared/hud.js header."),
    'widgets': widgets,
}


def overlap(a, b):
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


small = [w for w in widgets if w['type'] in ('text', 'icon')]
errs = ['overlap: %s / %s' % (a['id'], b['id']) for i, a in enumerate(small) for b in small[i + 1:] if overlap(a, b)]
if errs:
    print('\n'.join(errs))
    sys.exit(1)
with open(OUT, 'w') as f:
    json.dump(layout, f, indent=2)
    f.write('\n')
print('wrote %s: %d widgets' % (os.path.relpath(OUT, ROOT), len(widgets)))
