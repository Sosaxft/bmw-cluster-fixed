"""
gen_lcmap.py - writes apps/cluster_themes/hud/layouts/lcmap.json, the Live Cockpit Map cluster theme (shaders.js hexlc).

A copy of BMW's own iDrive 7 Live Cockpit screen with the map up (a straight photo of it, Nov 21 2026): the speed bracket
in blue on the left, the rev bracket in red on the right, the Waze map filling the hexagon between them, the speed and
the gear inside it, the slanted fuel and oil gauges in its lower corners, the clock, range and outside temperature in the
bottom strip. The brackets and the scale numbers take the Sport theme's numbers, traced off a real car's Live Cockpit
(sport.json); the speed, gear, gauges and run lengths come from the photo. Lettering: Redline's HUD's, squared digits
and Ubuntu (tools/bake_squared.py). The map fades out before it reaches the speed and the gear (HOLE, FADE).

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
# the map shows from HOLE and fades out over FADE px a side (left, top, right, bottom) into the hexagon's night blue,
# gone before the speed (x 385..625) and the gear (x 1370..1610)
# The map's window: between the speed and the gear, clear of the gauges, the map's own shape (1088x480 -> 764x337). It
# is written as the layout window (waze.js; "mapWindow"): eroobeeroo's Waze on Cluster then draws the map ON the
# theme there, so BMW's own map screen under the theme (its speed readout, shading, the M display's dark boxes) never
# shows; "mapfade" fades its edges over it. With a Waze on Cluster that doesn't read the window (robertnisipeanu's
# 0.11) the theme opens the same window onto the map slot instead, where BMW's map screen does show.
# Drawn over the theme (the layout window) the map fills the panel behind the whole hexagon, at its own shape
# (1088x480 x 1.29), the theme drawn over it as an overlay: the map fades in from the hexagon's inner line, dimmed
# outside it, darker behind the speed and the gear. Under the theme (0.11, the map slot) the window is BMW's map slot.
MAPWIN = [257, 40, 1405, 620]
# Under the theme (0.11) the window starts past BMW's own speed readout left of the map ("mph", car photo Nov 21 2026:
# x ~600..712), which BMW's map screen draws there; drawn over the theme (holeOver) nothing of BMW's shows
HOLE = [690, 120, 814, 480]
FADE = [90, 60, 120, 50]
SCRIM = [505, 1490, 336, 172]          # the speed's and the gear's centres x, y; the oval's half width (its height x 0.4)

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
    # every readout an overlay: over the theme's own layer (an overlay too, z 0) and over the map when it is drawn on
    # the panel (the layout window: a content layer, z 900)
    d = {'id': id_, 'type': 'text', 'class': 'overlay', 'z': 5, 'x': x, 'y': y, 'w': w, 'h': h, 'text': tx, 'font': font, 'color': color,
         'align': align}
    d.update(kw)
    return d


def icon(id_, name, x, y, w, h, color='dim'):
    return {'id': id_, 'type': 'icon', 'icon': name, 'class': 'overlay', 'z': 5, 'x': x, 'y': y, 'w': w, 'h': h, 'color': color}


widgets = [{
    # the backdrop round the hexagon (no flat black): washes, a weave, light rails over the top and along the bottom
    'id': 'bg', 'type': 'lcbg', 'class': 'ambient', 'z': 0, 'x': 0, 'y': 0, 'w': W, 'h': H, 'rails': [46, 644, 760, 0.85],
    'hole': HOLE, 'holeOver': MAPWIN, 'holeWhen': 'mapUp', 'holeInset': 0, 'fade': FADE,
}, {
    'id': 'lc', 'type': 'hexlc', 'class': 'overlay', 'z': 0, 'x': 0, 'y': 0, 'w': W, 'h': H,
    'geo': GEO, 'k': K, 'band': BAND, 'inner': INNER, 'scale': SCALE, 'ticks': TICKS, 'rpmMax': RPM_MAX,
    'fuelSeg': FUEL_SEG, 'oilSeg': OIL_SEG, 'strip': [BOTTOM_END, 0, 0, 0], 'topEnd': TOP_END,
    'hole': HOLE, 'holeOver': MAPWIN, 'holeWhen': 'mapUp', 'holeInset': 0, 'holeRadius': 6, 'fade': FADE, 'scrim': SCRIM,
}]
for i, (x, y) in enumerate(SPD):
    widgets.append(text('spd%d' % i, x, y, 110, 26, '{{spd:%d}}' % i, 'q_scale', 'lscale', 'right',
                        near=['speed', i], nearColor='fg'))
for i, (x, y) in enumerate(RPM):
    widgets.append(text('rpm%d' % i, x, y, 60, 26, str(i), 'q_scale', 'lscale', 'left', near=['rpm', i], nearColor='fg'))
widgets += [
    text('mph_cap', 338, 88, 80, 25, '{{u:speedLc}}', 'u_cap', 'lblue'),
    text('rpm_cap', 1442, 88, 200, 25, '1/min x 1000', 'u_cap', 'lred'),
    text('badge', 810, 48, 300, 25, '{{badge}}', 'u_cap', 'dim'),
    text('mode', 710, 80, 500, 28, '{{mode}}', 'u_mode', 'modeComfort', colorBy='mode'),
    # the drive mode over the hexagon's top, in its colour (BMW's: SPORT red, COMFORT blue, ECO PRO green)
    # inside the hexagon: the speed on the left, the gear on the right (the photo)
    text('speed', 372, 305, 266, 62, '{{speed}}', 'q_big', 'fg'),
    text('speed_unit', 455, 374, 100, 25, '{{u:speedLc}}', 'u_cap', 'dim'),
    text('gear', 1404, 305, 172, 62, '{{gear}}', 'q_big', 'fg', hotWhen='now'),
    # the fuel and oil gauges' ends and icons (the Sport theme's, kept up with the map as on BMW's screen)
    # the fuel and oil gauges: thick slanted bars (shader), three numbers along each and the icon (as the photo)
    text('f_full', 393, 407, 60, 29, '1', 'u_small', 'fg'),
    text('f_half', 448, 485, 60, 29, '1/2', 'u_small', 'fg'),
    icon('fuel_icon', 'fuel', 512, 485, 22, 26),
    # the range beside the fuel gauge, the oil temperature beside the oil gauge
    text('f_range', 532, 525, 58, 29, '{{range}}', 'u_small', 'fg', 'right'),
    text('f_range_u', 593, 527, 30, 25, '{{u:distLc}}', 'u_cap', 'dim', 'left'),
    text('f_empty', 503, 563, 60, 29, '0', 'u_small', 'fg'),
    text('o_hot', 1467, 407, 60, 29, '{{temp:150}}', 'u_small', 'fg'),
    text('o_mid', 1412, 485, 60, 29, '{{temp:100}}', 'u_small', 'fg'),
    icon('oil_icon', 'oilcan', 1370, 522, 34, 22, 'lblue'),
    text('o_now', 1290, 528, 76, 29, '{{oil}}°', 'u_small', 'fg', 'right'),
    text('o_cold', 1357, 563, 60, 29, '{{temp:50}}', 'u_small', 'fg'),
    # the bottom strip, as the Sport theme (BMW's gear letter shows in the gap x 1380..1460)
    {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60, 'color': 'strip', 'stripRow': 'l'},
    {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60, 'color': 'strip', 'stripRow': 'r'},
    text('strip_time', 120, 678, 124, 26, '{{time}}', 'u_val', 'fg', 'right', stripRow='l'),
    text('strip_ampm', 250, 680, 35, 25, '{{ampmLc}}', 'u_cap', 'dim', 'left', stripRow='l'),
    # (the range sits by the fuel gauge)
    text('strip_out', 1676, 678, 80, 26, '{{ambient}}', 'u_val', 'fg', 'right', stripRow='r'),
    text('strip_out_u', 1762, 680, 27, 25, '{{u:temp}}', 'u_cap', 'dim', 'left', stripRow='r'),
]

layout = {
    'schemaVersion': 2,
    'name': 'Live Cockpit Map',
    'theme': 'lcmap',
    'mapLive': True,
    'mapWindow': MAPWIN,
    '_about': ("A copy of BMW's own iDrive 7 Live Cockpit screen with the map up, generated by tools/gen_lcmap.py (edit that "
               "and regenerate). One hexlc effect layer draws the black backdrop, the blue speed bracket (0..200 mph) and the "
               "red rev bracket (0..7000), each a bold outer line, a band shaded inwards and lit to the value and an inner "
               "line, with their top and bottom runs, and the slanted fuel and oil gauges in the lower corners. While the "
               "map shows inside the theme ('mapUp': Maps on cluster, CarPlay's Apple Maps / Waze / Google Maps) the hexagon's "
               "inside shows it through the middle of BMW's map window, fading out into the night blue before the speed "
               "and the gear, without a rebuild (mapLive); otherwise it stays a dark night-map blue. Each bracket's colour glows in over the map's edges. The "
               "brackets, scale numbers and gauges are the Sport theme's, traced off a real car; the speed and gear sit "
               "inside the hexagon as in the photo; the clock, range and outside temperature in the bottom strip, BMW's "
               "gear letter left uncovered. Widget reference: shared/hud.js header."),
    'widgets': widgets,
}


def overlap(a, b):
    return a['x'] < b['x'] + b['w'] and b['x'] < a['x'] + a['w'] and a['y'] < b['y'] + b['h'] and b['y'] < a['y'] + a['h']


small = [w for w in widgets if w['type'] in ('text', 'icon')]
def apart(a, b):   # never on screen together (now playing / the clock)
    return {a.get('showWhen'), b.get('showWhen')} == {'media', '!media'}


errs = ['overlap: %s / %s' % (a['id'], b['id']) for i, a in enumerate(small) for b in small[i + 1:] if overlap(a, b) and not apart(a, b)]
if errs:
    print('\n'.join(errs))
    sys.exit(1)
with open(OUT, 'w') as f:
    json.dump(layout, f, indent=2)
    f.write('\n')
print('wrote %s: %d widgets' % (os.path.relpath(OUT, ROOT), len(widgets)))
