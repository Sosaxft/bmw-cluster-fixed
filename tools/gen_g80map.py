"""
gen_g80map.py - writes apps/cluster_themes/hud/layouts/g80map.json, the G80 Map cluster theme (shaders.js g80).

The G80 / G82 M3 and M4's head-up display as Redline draws it (redline/hud-m.js drawRamp, "Ramp"), scaled up 4x onto
the cluster panel: the thick cream rev rail climbing from the 0 at the bottom left, bending round a wide knee and running
flat over the top, its tabs every 1000 rpm, the cream rev band and red needle under it, the 8 slanted shift lights over
the flat part; the gear in squared digits under the knee with D / S / M beside it, a line, the speed under it; the oil,
water and boost readouts on the right. In the middle the Waze map, fading out into the black before it reaches the gear
and speed on the left and the readouts on the right. Squared digits and Ubuntu, Redline's lettering
(tools/bake_squared.py).

Every number below is Redline's HUD geometry (hud-m.js RP, RD, RL, the gear and readout placings) through X() / Y().
Edit and run:   python3 tools/gen_g80map.py      (it refuses overlapping text boxes)
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'apps', 'cluster_themes', 'hud', 'layouts', 'g80map.json')

W, H = 1920, 660
S, OX, OY = 4.0, 12, 34          # Redline's 400x130 HUD picture -> panel px


def X(h): return round(S * h + OX, 1)
def Y(h): return round(S * h + OY, 1)


RPM_MAX = 8000
# hud-m.js RP: the rail's top edge from (x0, y0) up to the knee (kx, ky), flat to x1; kr the knee's radius
RAIL = [X(38), Y(72), X(90), Y(22), X(372), S * 44]
# RD: rail 3.4, band from 4.4 to 13.4 under the top edge, 1.0 gap round a tab
BAND = [S * 3.4, S * 4.4, S * 13.4, S * 1.0]
TAB = [S * 2.7, S * 2.1, S * 4.8, S * 1.5]
V = [S * 1.5, S * 3.0, S * 2.2, S * 2.4]
# RL: 8 lights over the flat part, leaning right by 10
LIGHTS = [X(121), X(372), Y(3.5), Y(18.5), S * 10]
# BMW's map window (mapcal.json) is 416,120 1088x480; the map shows from here and fades out over FADE a side, so it
# never reaches the gear and speed (left) or the readouts (right)
HOLE = [640, 130, 760, 470]
FADE = [170, 120, 160, 80]


def rail_path():
    x0, y0, kx, ky, x1, kr = RAIL
    cl = math.hypot(kx - x0, ky - y0)
    u = ((kx - x0) / cl, (ky - y0) / cl)
    turn = math.acos(u[0])
    dk = kr * math.tan(turn / 2)
    t1 = (kx - u[0] * dk, ky - u[1] * dk)
    c = (kx + dk, ky + kr)
    a0 = math.atan2(t1[1] - c[1], t1[0] - c[0])
    l1 = math.hypot(t1[0] - x0, t1[1] - y0)
    la = kr * (-math.pi / 2 - a0)
    total = l1 + la + (x1 - c[0])

    def at(s):
        if s <= l1:
            return (x0 + u[0] * s, y0 + u[1] * s)
        if s <= l1 + la:
            a = a0 + (s - l1) / kr
            return (c[0] + kr * math.cos(a), c[1] + kr * math.sin(a))
        return (c[0] + (s - l1 - la), ky)
    return at, total


def text(id_, x, y, w, h, tx, font, color, align='center', **kw):
    d = {'id': id_, 'type': 'text', 'z': 5, 'x': round(x), 'y': round(y), 'w': round(w), 'h': round(h), 'text': tx,
         'font': font, 'color': color, 'align': align}
    d.update(kw)
    return d


def fill(id_, x, y, w, h, color, **kw):
    d = {'id': id_, 'type': 'fill', 'class': 'content', 'z': 5, 'x': round(x), 'y': round(y), 'w': round(w), 'h': round(h), 'color': color}
    d.update(kw)
    return d


widgets = [{
    'id': 'g80', 'type': 'g80', 'class': 'content', 'z': 1, 'x': 0, 'y': 0, 'w': W, 'h': H,
    'rail': RAIL, 'band': BAND, 'tab': TAB, 'v': V, 'lights': LIGHTS, 'rpmMax': RPM_MAX,
    'hole': HOLE, 'holeWhen': 'mapUp', 'holeInset': 0, 'fade': FADE,
}]

# the scale: 0 2 4 6 8 in squared digits (10 tall on the HUD), the 0 under the climb's start, the rest under the band
at, total = rail_path()
SC_H = 42                         # g_scale's cell
for r in range(0, RPM_MAX + 1, 2000):
    px, py = at(r / RPM_MAX * total)
    y = py + S * 8 if r == 0 else RAIL[3] + BAND[2] + S * 4
    widgets.append(text('sc%d' % (r // 1000), px - 40, y - 2, 80, SC_H, str(r // 1000), 'g_scale', 'fg'))

GX = X(113)                                   # the gear's centre
FOOT = Y(90)                                  # the gear's foot, level with the 0's
widgets += [
    # the gear (27 tall on the HUD), D / S / M beside it, the line under it and the speed under that
    text('gear', GX - 85, FOOT - 116 + 2, 170, 116, '{{gearnum}}', 'g_gear', 'fg', hotWhen='now'),
    text('prog', X(135), Y(63) + 2, 60, 41, '{{prog}}', 'u_mode', 'dim', 'left'),
    fill('gear_line', X(63), Y(95), X(147) - X(63), 6, 'fg'),
    text('speed', X(105) - 170, Y(101), 340, 88, '{{speed}}', 'g_speed', 'fg'),
    text('speed_u', X(150), Y(99) + 2, 90, 37, '{{u:speedLc}}', 'u_unit', 'dim', 'left'),
]
# the readouts on the right, past the map's fade: label left, value right (Redline's rows 2-4, 21 apart)
ROWS = [('OIL', '{{oil}}', '{{u:temp}}'), ('WATER', '{{coolant}}', '{{u:temp}}'), ('BOOST', '{{boost}}', '{{u:boostLc}}')]
RX0, RX1 = 1420, 1800
for k, (lab, val, unit) in enumerate(ROWS):
    y = Y(68 + k * 21) - 14
    widgets += [
        text('r%d_l' % k, RX0, y + 14, 120, 31, lab, 'u_label', 'dim', 'left'),
        text('r%d_v' % k, RX0 + 122, y, RX1 - 66 - RX0 - 122, 56, val, 'g_val', 'fg', 'right'),
        text('r%d_u' % k, RX1 - 62, y + 12, 62, 37, unit, 'u_unit', 'dim', 'left'),
    ]
widgets += [
    # the bottom strip: clock, range, outside (BMW's gear letter shows in the gap x 1380..1460)
    {'id': 'strip_cover_l', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 0, 'y': 660, 'w': 1380, 'h': 60, 'color': 'bg', 'stripRow': 'l'},
    {'id': 'strip_cover_r', 'type': 'fill', 'class': 'content', 'z': 0, 'x': 1460, 'y': 660, 'w': 460, 'h': 60, 'color': 'bg', 'stripRow': 'r'},
    text('strip_time', 110, 676, 134, 30, '{{time}}', 'u_val', 'fg', 'right', stripRow='l'),
    text('strip_ampm', 250, 676, 50, 37, '{{ampmLc}}', 'u_unit', 'dim', 'left', stripRow='l'),
    text('strip_range', 330, 676, 130, 30, '{{range}}', 'u_val', 'fg', 'right', stripRow='l'),
    text('strip_range_u', 466, 676, 50, 37, '{{u:distLc}}', 'u_unit', 'dim', 'left', stripRow='l'),
    text('strip_out', 1640, 676, 110, 30, '{{ambient}}', 'u_val', 'fg', 'right', stripRow='r'),
    text('strip_out_u', 1756, 676, 50, 37, '{{u:temp}}', 'u_unit', 'dim', 'left', stripRow='r'),
]

layout = {
    'schemaVersion': 2,
    'name': 'G80 Map',
    'theme': 'g80map',
    'mapLive': True,
    '_about': ("The G80 M3 / M4 head-up display's look (Redline's Ramp, redline/hud-m.js) on the cluster, generated by "
               "tools/gen_g80map.py (edit that and regenerate). One g80 effect layer draws the cream rev rail climbing from "
               "the 0 at the bottom left and running flat over the top with a tab every 1000 rpm, the cream rev band and "
               "red needle under it, the red zone, the peak and the 8 slanted shift lights over it. While the map shows "
               "('mapUp': Maps on cluster, CarPlay's Apple Maps / Waze / Google Maps) it shows through the middle of BMW's "
               "map window and fades out into the black before the gear and speed (left) and the readouts (right), "
               "without a rebuild (mapLive). Lettering: squared digits and Ubuntu, as Redline's HUD. Widget reference: "
               "shared/hud.js header."),
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
