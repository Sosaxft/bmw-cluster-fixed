# Patched bimmer-lab/apps — HmiMediaState install fix

Fork of bimmer-lab/apps with the fix for the install error:

> cluster_themes 0.19.0 cannot be installed on this head unit: its SOME/IP
> manifest asks for what the unit does not have (...HmiMediaState: instance
> "1" is not on this unit (it has HMI_CID, HMI_FoMo_Left, HMI_FoMo_Right))

## What was wrong
0.19.0 added the `HmiMediaState` service (the Vector theme's "now playing"
music panel) without naming which instance to use, so the build defaulted to
instance `"1"`. These head units don't have an instance named `"1"` — the
front screen's instance is named `HMI_CID`. BMW's app manager then refused the
whole app.

## What changed (3 edits)
1. `apps/cluster_themes/app.json` — added `"_instances": "HMI_CID"` to the
   HmiMediaState signal.
2. `apps/idrive_hud_widgets/app.json` — same.
3. `kit/runtime/car.js` — the runtime watched every interface at `"1"`; now it
   reads HmiMediaState from `HMI_CID` (front screen) so the music panel still
   works. Everything else stays on `"1"`.

Versions bumped: cluster_themes 0.19.0 → 0.19.1, idrive_hud_widgets 0.15.0 → 0.15.1.

Nothing else touched — all themes and the shift-light/HUD logic are unchanged.

## 0.20.0 — new theme: Hex Map
After BMW's Live Cockpit Sport view with the map in the middle. Pick **Hex Map** in Cluster Themes.
- A hexagon frame (white line, band glowing red to orange, orange inner line): speed scale on the left
  side, revs on the right with yellow / red redline marks; the number nearest the needle lights orange.
- The Waze map fills the hexagon (needs waze-on-cluster and "Show Waze map inside the theme" on). The cut
  never goes past BMW's map window, so BMW's own gauges can't peek through. With no map, an animated road
  runs in the hexagon.
- Speed, fuel bar and range on the left; gear (S2 / D3 / P), drive mode, oil-temperature bar on the right;
  boost and coolant under the hexagon; clock and outside temperature in the bottom strip.
- New files: `shared/shaders.js` HEXDASH (same inputs as the Sport shader, about the same cost),
  `hexdash` colours in `shared/hud_themes.js`, layout written by `tools/gen_hexmap.py` (edit and rerun it to
  re-tune; it refuses to write a layout with overlapping parts), preview picture for the theme picker.
- Reverted the 0.19.2 mview "center cover": it was based on a misread of the mview geometry and would have
  blocked a strip of mview's map window. mview is back to exactly the original.

## 0.20.1 — less delay, Hex Map restyle
- Less delay on every theme: speed, gear, revs and boost redraw every 100 ms (was 200 ms), and the rev counter's
  smoothing is 60 ms (was 120 ms). Other readouts stay at 200 ms.
- Hex Map: clean Outfit lettering (new h_* fonts, nothing else's fonts changed), black backdrop with the orange glow
  only along the inner edges and on the lit part (the car brightens dark reds, so no dark-red slabs), thinner white
  lines, a road of lines only, and a wider hexagon filling BMW's whole map window with speed / gear at the edges.

## 0.21.0 — new theme: Live Cockpit Map
A copy of BMW's own iDrive 7 Live Cockpit screen with the map up. Pick **Live Cockpit Map** in Cluster Themes.
- Blue speed bracket left, red rev bracket right (bold outer line, band shaded inwards and lit to the value, inner
  line, top and bottom runs), the Waze map filling the hexagon (past the map window, a dark night-map blue so it reads
  as one map), the speed and gear big inside it, the slanted fuel and oil gauges in its lower corners over the map.
- The brackets and scale numbers are the Sport theme's, traced off a real car; the rest measured on a straightened
  photo of BMW's screen. Barlow lettering (closest open font to BMW's), new l_* fonts.
- New: shaders.js HEXLC (same inputs as Sport / Hex Map), `lcmap` colours, layout written by tools/gen_lcmap.py.

## 0.21.1 — Live Cockpit Map, closer to BMW's (v1 kept on branch backup-lcmap-v1)
- Lettering: Inter (SIL OFL, tools/fonts-src/Inter-OFL.txt), a grotesque like BMW's own; new l_* fonts.
- Shades: each bracket's blue / red glows in over the map's edges; the bands have a lit rim at their outer edge.
- Fuel and oil gauges as BMW's: thick white slanted bars, the oil bar's cold end blue, three numbers along each
  (1 / 1/2 / 0, 300 / 210 / 120 °F), moved off the brackets.
- No road: with no map up, the hexagon stays a dark night-map blue. The map itself comes from Maps on cluster
  (robertnisipeanu/idrive-apps): CarPlay's Apple Maps, Waze or Google Maps.

## HUD Widgets 0.16.0 / Cluster Themes 0.21.2 — turn-signal arrows on the HUD, safer installs
- HUD: green arrows in the top corners of the HUD's window flash with your turn signals (left, right) and with the
  hazards (both), at BMW's rate; nothing shows while they're off. Setting "Turn-signal arrows" (on by default).
  Read from de.bmw.body.Light StatusFunctionsIndicators (shared/turn.js), added to every HUD layout but the
  calibration ones (hud.js TURN_WIDGET, shaders.js TURN).
- Installs: kit/tools/build.py now has fit_to_unit (from cauliflowermossgrape/idrive7-apps): when the Store builds an
  app on the head unit, anything the unit's own SOME/IP catalog lacks (an interface marked _optional, an instance, a
  field) is left out instead of BMW refusing the whole app. A unit without the turn-signal interface installs as
  before; the arrows just never light.
- bench/run-app.js: manual `turn` (left / right / hazard / off) feeds the turn signals.

## HUD Widgets 0.16.1 — "Blinkers only" layout
- New layout "Blinkers only" (first after Off in every layout list): adds nothing but the turn-signal / hazard arrows,
  so BMW's own HUD stays exactly as it is with the arrows flashing in its top corners.

## Cluster Themes 0.21.3 — Live Cockpit Map closer to BMW's
- The speed / rev bands are now one continuous shaded band from the bright outer line to the inner line (no black gap),
  as on BMW's screen.
- A thick bar under each bracket's bottom run, bright at the bracket and fading toward the middle.
- Fuel and oil gauges redrawn like BMW's: thinner, square-ended and cut into short segments, dim where empty.

## HUD Widgets 0.17.0 — Redline built in
- The whole Redline app (cauliflowermossgrape/idrive7-apps apps/redline, MIT, commit a948390) now runs inside HUD
  Widgets, in the same process (apps/idrive_hud_widgets/redline/, with its own kit; main.js starts it, screen_mux.js
  shares the centre screen). Redline can be uninstalled: one app starts with the car and has the HUD.
- Redline's HUD shows where its settings say and the widgets everywhere else: by default its G80 M3 / M4 "Ramp" HUD
  is on in Sport, and Comfort / Eco Pro keep the widgets' layout (the widgets step aside while Redline's tach holds
  the HUD, kit hud_claim). Redline no longer turns its own HUD off at switch-off (hudHandBack off by default here).
- Every Redline setting is in the settings list as "Redline: ..." (tools/merge_redline.py merges its app.json);
  hudX / hudY / redline are rlHudX / rlHudY / rlRedline so they don't clash with the widgets' own.
- Centre screen: the bar's "Redline / Widgets" button, or setting "Centre screen page", flips between the widgets'
  page and Redline's (Tach, Shift log, Learned, HUD looks).
- build.py: app.json "codeDirs" ships folders of code as they are; settings marked "hidden" stay out of the list.
- Bench: BENCH_PAGE_PNG=<file> saves the centre screen's picture.

## Cluster Themes 0.22.1 — Live Cockpit Map: Redline's lettering, the map fades out
- 0.22.0's G80 Map theme is taken out again (not what was asked for).
- Live Cockpit Map now uses the Redline HUD's lettering: squared digits for the speed, the gear and the scale numbers
  (fonts q_*, tools/bake_squared.py, after redline/hud-m.js sqGlyph) and Ubuntu for the rest (fonts u_*).
- The map no longer runs under the speed and the gear: it shows through the middle of the hexagon and fades out into
  its night blue on every side (hexlc u_fade; gen_lcmap.py HOLE / FADE), the brackets' blue and red glowing over its
  edges as before.

## Cluster Themes 0.22.2 — Live Cockpit Map: a bigger map
- The map shows over more of the hexagon (x 612..1408, all of BMW's map window's height) and fades out over a shorter
  edge (105 px a side, 55 top, 45 bottom), still clear of the speed and the gear.
