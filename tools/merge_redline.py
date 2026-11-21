#!/usr/bin/env python3
"""Merge the Redline app's app.json (apps/idrive_hud_widgets/redline/app.redline.json, upstream as it is) into
HUD Widgets' app.json: HUD Widgets runs Redline (redline/, its start(ctx)) next to its own widgets, in one process.
Redline's HUD shows where it is set to (Sport by default) and the widgets everywhere else (hud_claim: the widgets step
aside while Redline's tach holds the HUD); the centre screen is either app's page (setting "centerPage", bar button).

  - settings: "centerPage" first, HUD Widgets' own, then Redline's (labels "Redline: ..."). Keys HUD Widgets already
    uses with another meaning are renamed in Redline's code: hudX -> rlHudX, hudY -> rlHudY, redline -> rlRedline.
    demo, shiftBefore and coldGuard mean the same in both and are shared.
  - signals: the union; an interface both name gets every field of both, and stays "_optional" only if both say so.
  - screens: MAIN gets Redline's buttons too (HUD Widgets hides them).
Run again after updating redline/ from upstream: python3 tools/merge_redline.py
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'apps', 'idrive_hud_widgets')
RENAME = {'hudX': 'rlHudX', 'hudY': 'rlHudY', 'redline': 'rlRedline'}
SHARED = ('demo', 'shiftBefore', 'coldGuard')
ENGINE = {'key': 'centerPage', 'label': 'Centre screen page', 'type': 'choice', 'default': 'widgets',
          'options': [['widgets', 'HUD Widgets'], ['redline', 'Redline']]}
# Redline defaults changed here: its G80 M3 / M4 "Ramp" HUD on (in Sport; Comfort keeps the widgets), and it never turns
# itself off at switch-off (upstream hands the HUD back to a standing app, which here is the widgets in the same app)
DEFAULTS = {'hud': 'on', 'hudStyle': 'ramp', 'hudHandBack': False}
SWAP = ['BTN_SWAP', 'Redline / Widgets']

a = json.load(open(os.path.join(APP, 'app.json')))
r = json.load(open(os.path.join(APP, 'redline', 'app.redline.json')))
own = [s for s in a['settings'] if s['key'] not in ('hudEngine', 'centerPage') and not s.get('_redline')]
keys = {s['key'] for s in own}
rl = []
for s in r['settings']:
    if s['key'] in SHARED:
        continue
    s = dict(s, key=RENAME.get(s['key'], s['key']), _redline=True)
    if s['key'] in DEFAULTS:
        s['default'] = DEFAULTS[s['key']]
    assert s['key'] not in keys, s['key']
    s['label'] = 'Redline: ' + s['label']
    rl.append(s)
a['settings'] = [ENGINE] + own + rl

sig = a['signals']
for iface, fr in r['signals'].items():
    if iface not in sig:
        sig[iface] = fr
        continue
    fa = sig[iface]
    for k, v in fr.items():
        if k == '_optional' or k.startswith('_') and k in fa:
            continue
        if k not in fa:
            fa[k] = v
        elif fa[k] != v and not k.startswith('_'):
            fa[k] = ''.join(sorted(set(fa[k] + v), key='rsw'.index))
    if '_optional' in fa and '_optional' not in fr:
        del fa['_optional']

main = next(s for s in a['screens'] if s['name'] == 'MAIN')
have = {b[0] for b in main['buttons']}
rmain = next(s for s in r['screens'] if s['name'] == 'MAIN')
main['buttons'] += [b for b in [SWAP] + rmain['buttons'] if b[0] not in have]
a['codeDirs'] = ['redline']
json.dump(a, open(os.path.join(APP, 'app.json'), 'w'), indent=2, ensure_ascii=False)
open(os.path.join(APP, 'app.json'), 'a').write('\n')
print('%d settings (%d Redline), %d interfaces, buttons %s' % (len(a['settings']), len(rl), len(sig), [b[0] for b in main['buttons']]))
