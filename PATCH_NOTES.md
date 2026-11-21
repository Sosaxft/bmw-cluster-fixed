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
