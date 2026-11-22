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

## Cluster Themes 0.23.0 — Live Cockpit Map: livelier, drive mode, next turn, richer gauges
- Livelier: brighter, more saturated blue and red brackets and bands (shaded less dark), a wider glow off the outer
  lines and over the hexagon's inside edge, a deep blue inside that lightens towards the top.
- The drive mode over the hexagon (SPORT red, COMFORT blue, ECO PRO green; text "colorBy": "mode", theme roles
  modeSport / modeComfort / modeEco).
- The next turn at the top of the map (arrow, distance, street) from CarPlay / Android Auto / BMW navigation: Redline's
  directions (shared/nav.js, hud_nav.js), setting "Next turn on the cluster" (while a route runs / near turns / off).
  Its interfaces are optional: a unit without them installs as before.
- Gauges: marks at 0, 1/4, 1/2, 3/4 and full, the fuel reserve marked red; the range beside the fuel gauge, the oil
  temperature beside the oil gauge.
- The shader sheds the unused road (8472 tokens, about what 0.21 had).

## Cluster Themes 0.23.1 — works with Maps on cluster 0.11; no turn arrow
- Maps on cluster 0.11 (waze-on-cluster 0.11.0, Nov 20 2026) dropped the "start panel" command the themes used: the map
  now always goes on the cluster's own map slot, as with BMW's own Map view. waze.js reads its new status line (a
  "cluster" field) and, with it, sends nothing: the theme's window opens while the map shows on the cluster, and the
  map shows through it exactly where BMW's Map view puts it. Older versions are handled as before.
  Needs, as with the stock cluster: Maps on cluster's Show on set to Cluster, and the car's Instrument cluster >
  Central display area set to Map view.
- The next-turn arrow on Live Cockpit Map is gone again (the map itself shows the road); its interfaces and setting
  are out of Cluster Themes.
- bench/fake-waze.js --v11 behaves as 0.11.

## Cluster Themes 0.23.2 — Live Cockpit Map: blends with a dark map, covers BMW's map-view boxes
- Dark only, made to blend with CarPlay's / Waze's dark map: the backdrop is the near-black blue-grey of a night map
  (not pure black), the hexagon's inside the dark map's own blue-grey, the bottom strip the same tone.
- BMW's own Map view draws two dark boxes over the map that the window showed (a photo in the car, Nov 21 2026): two
  opaque cards now cover them (new image widget "card", icons.js paintCard; theme roles card / cardLine). The middle
  one shows what's playing (title, artist), else the clock; the right one the drive mode in its colour. The clock moved
  from the strip onto the card. The map now starts fading at x 690, past BMW's own "mph" left of it.

## Cluster Themes 0.23.3 / HUD Widgets 0.17.1 — faster, no cover cards
- Faster: the gauges, bars and shift lights update up to 60 times a second (TICK_MS 50 -> 16; a uniform goes only
  when its value changes), the speed / gear / rpm texts 30 times a second (LIVE_TEXT_MS 100 -> 33, cluster-render's
  limit for an image layer), the rev smoothing 60 -> 35 ms. CPU on the bench unchanged.
- Live Cockpit Map: 0.23.2's cards over BMW's map-view boxes are gone again (they only hid the boxes); the clock is
  back in the strip, the drive mode back over the hexagon. The dark-map tone stays.

## Cluster Themes 0.23.4 — cluster diagnostics
- Setting "Cluster diagnostics" (Settings tab): while on, the tab shows cluster-render's own status, asked for every
  3 s: the targets, what each of the KOMBI's slots holds, the guide hold, the budget (layer lines left out), to
  photograph with a theme on and with it off. For the black boxes over the map that show only while a theme is on
  (Nov 21 2026). shared/hud.js clusterDiagLines, page.js settingsTab.

## Cluster Themes 0.24.0 — the map drawn over the theme (no BMW map screen, no M display boxes)
- The dark boxes over the map (BimmerCode's M display) are BMW's own map screen, which the KOMBI draws over the map in
  its map slot, under any theme: a theme's window onto that slot shows them. Fix, as ZEKAI's ID7 Cluster Themes does:
  the layout window (eroobeeroo's Waze on Cluster 0.9.107+, layout_window.h): while a map theme shows, waze.js keeps
  /dev/shm/cluster-info/map_window.txt ("panel X Y W H", a lease, touched every second, removed when not wanted), and
  that Waze on Cluster draws the map on the panel in that rect, ABOVE the theme, where nothing of BMW's shows.
  waze.js sends no "start" while it holds the window; the status reads "Map showing over the theme".
- Live Cockpit Map: its map window is 764x337 between the speed and the gear (the map's own shape, clear of the gauges;
  layout "mapWindow"), and a new overlay "mapfade" (shaders.js, 216 tokens) fades the map's edges into the theme's
  own colours round it. With robertnisipeanu's 0.11 (no window support) the theme opens the same window onto the map
  slot, as before.

## Cluster Themes 0.24.1 — Live Cockpit Map: one picture, the map behind the whole theme
- With a Waze on Cluster that reads the layout window, the map now fills the panel behind the whole hexagon
  (257,40 1405x620, its own shape) and the theme is drawn over it as one overlay (hexlc now class overlay, the
  readouts overlays above it): the map fades in from the hexagon's inner line, shows dimmed outside the hexagon, fades
  out at the window's edges, and is darker behind the speed and the gear (u_scrim) so they read; no separate box.
  "holeOver" is the window while the map is drawn over the theme ("mapOver", waze.js over); BMW's map slot otherwise.
  The "mapfade" overlay is no longer used by it. hexlc: 8555 tokens.
- bench/page.html ?mapover=x,y,w,h: a stand-in dark map in that rect.

## Cluster Themes 0.24.2 — Live Cockpit Map: no empty black round the dash
- A backdrop layer under the hexagon (new effect "lcbg", class ambient, 570 tokens): a deep blue-grey lifted in the
  middle, the speed side washed blue and the rev side red from the brackets, a faint diagonal weave, light rails over
  the top (y 46) and along the bottom (y 644), blue to white to red, fading at their ends, darker at the screen's very
  edges. hexlc is now see-through round the hexagon (it was opaque near-black there). The strip a touch lighter.
  See-through in the map's window like the hexagon's layer.

## HUD Widgets 0.18.0 — turn-signal arrows over Redline's HUD
- New setting "Turn-signal arrows over Redline's HUD" (on by default, in the page's Settings with "Turn-signal arrows"):
  while Redline's HUD has the HUD (Sport by default), the widgets no longer step aside completely: the "Blinkers only"
  layout stays up, so the green arrows flash in the HUD window's top corners over Redline's picture (clear of its
  tach). shared/hud.js _turnOverClaim; the status line says so.

## Cluster Themes 0.25.0 — Live Cockpit Map: BMW's digits, the map round the speed and gear
- Digits redrawn after BMW's own cluster (a photo of the car's stock M display, Nov 21 2026): squared with rounded
  corners, wide for the speed and the gear (1.3 x the height), narrow for the scale numbers (0.78), the 7 with a
  slanted stem (tools/bake_squared.py: per-font width, stroke and rounding). The words (mph, 1/min x 1000, the gauges'
  numbers, the strip, the drive mode) in Inter, the closest open font to BMW Type Next.
- The map is no longer cleared in a box: it fills the hexagon and is cut away only in an oval round the speed and
  round the gear (gone behind them, back above and below them), as on BMW's own map view. hexlc 8539 tokens.

## Store catalog — no GitHub API needed to see updates
- mgu-repo.json lists the two apps as "components" instead of the "apps/*" folder pattern: the Store lists a folder
  pattern through GitHub's API (60 requests an hour per address without a sign-in; a phone hotspot's address is shared),
  and when that limit refuses it the source keeps its old listing (mgu-updater sources.js repoEntries), which held the
  car at Cluster Themes 0.23.1. Components are read from GitHub's web hosts only, which that limit does not count.

## Cluster Themes 0.25.1 — Live Cockpit Map: no second speed beside the speed
- With a Waze on Cluster that draws the map under the theme (robertnisipeanu's 0.11), the theme's window onto BMW's map
  slot now starts at x 690, past BMW's own map-screen speed readout ("mph", x ~600..712), so it no longer shows beside
  the theme's speed. Drawn over the theme (the layout window) the window is unchanged.

## Cluster Themes 0.25.2 — a test for BMW's black boxes
- With Maps on cluster removed the two boxes still show (car photo Nov 21 2026), over a theme that is opaque there: they
  are BMW's own, drawn ABOVE the panel (BimmerCode's M display; the right one where its big gear letter sits). On an X3
  BMW drew such a box only while a theme covered its gear letter in the bottom strip. New test switch "Leave BMW's
  bottom strip uncovered (test)" (stripClear): no strip row and no strip covers, BMW's strip as it is, to see whether
  covering something of the M display's strip is what makes BMW draw them.

## Cluster Themes 0.25.3 — the black-box check runs by itself
- "Black-box check" (was "Cluster diagnostics"), once per switch-on, about 20 s: (1) cluster-render's slot report with
  the theme up; (2) the theme taken off for 5 s, BMW's own screen, and the report again; lines that differ are starred
  in Settings, so BMW's slots shown only while a theme is up stand out; (3) 8 s of one opaque blue sheet over all of
  the theme, no see-through parts. Black boxes still on the blue are BMW's, drawn above the panel; gone, BMW's
  cluster was showing through a see-through part of the theme. Then the theme comes back.

## Cluster Themes 0.25.4 — Live Cockpit Map blends edge to edge; a four-step black-box check
- Live Cockpit Map's backdrop is one even slate tone over the whole screen (the hexagon's own inside colour), with no
  darkened edges or corners, and BMW's bottom strip is covered in the same tone, so nothing reads as black around the dash.
- Car photos Nov 22 2026: the boxes show in D and go in M (manual), flickering on every shift. Every layer of Live
  Cockpit Map was listed (bench): both backdrops are opaque there and nothing of ours has an edge there, so BMW draws
  them on top of the panel. "Black-box check" now runs four steps, about 7 s each, to watch in D: 1 the theme;
  2 the theme with BMW's strip gap by the gear letter filled in; 3 one plain full-screen image layer and nothing else,
  the way ZEKAI's themes draw (which show no boxes); 4 BMW's own screen. Which steps show the boxes says what of ours
  sets BMW off.

## Cluster Themes 0.26.0 — BMW's black boxes fixed; Live Cockpit Map's map, gauges and lettering
- The black boxes: covering BMW's bottom strip is what makes BimmerCode's M display draw them over the middle in D (car
  photo Nov 22 2026, with "Leave BMW's bottom strip" on: gone). The switch is now on by default, for every theme:
  BMW's strip shows as it is (its range, clock, street and outside temperature), and a readout of ours that BMW's strip
  shows already ("stripTwin": Live Cockpit Map's range by the fuel gauge) is left out, so nothing shows twice.
- Live Cockpit Map's map: the window is centred between the speed and the gear and fades into both the same way (150 px
  a side, and a soft oval round each number). The speed and the gear moved in (x 560 / 1360, mirrored), over BMW's own
  map-screen readouts that showed under the theme on the gear side.
- Darker pockets at the screen's far ends, behind BMW's own lights (PARK), as on BMW's screen, instead of the flat tone.
- The fuel and oil gauges: slim even bars on a faint track, lit solid (fuel red when low, oil blue when cold, red when
  hot), three short marks on the numbers' side; no more dashed segments with marks across.
- Lettering: the D has a straight left side and a rounded right side (it read as a 0), the M is upright with a V, the 4
  is the squared 4.

## Cluster Themes 0.26.1, HUD Widgets 0.18.1 — readouts that keep up with the car
- "Still really delayed" (Nov 22 2026). Two causes, both fixed the way ZEKAI's themes (which never trailed) do it:
  - The car notifies speed and revs only now and then; the apps waited for those notifications. Speed and revs are now
    also read every 50 ms between them (skipped while a notification came in the last 120 ms; a read older than a
    notification is dropped), acceleration every 100 ms; the temperatures stay at 2.5 s. Both apps (the shared kit).
  - Live Cockpit Map's speed and gear were pictures re-drawn and uploaded on every change, queued behind cluster-render's
    image upload budget. They are now drawn by the GPU from the font's atlas (new widget "gtext"): a new value is one
    small uniform message, sent the moment it changes.

## Cluster Themes 0.26.2 — Live Cockpit Map's speed and gear show again
- 0.26.1's GPU-drawn speed and gear (gtext) did not show on the car (video Nov 22 2026): the shader named its glyph
  positions u_p, a name cluster-render keeps for its own projection matrix, so it did not link and drew nothing. Renamed
  u_pos. The bench now refuses a shader declaring any of the renderer's names (u_mvp, u_mv, u_m, u_v, u_p, u_normal) as
  anything but a mat4, as the car does, so this cannot pass the bench again.

## Cluster Themes 0.26.3, HUD Widgets 0.18.2 — revs that move with the engine
- "Rpms still look slow and delayed" (Nov 22 2026). The head unit gets the revs from the car only a few times a second
  (BMW's own cluster reads them straight off the engine), so even read as often as it can be, the tach stepped behind.
  Between two readings the revs now carry on at the rate of the last two (at most 12000 rpm/s), for at most one
  reading's gap and 250 ms, then hold where the car said; the 35 ms smoothing stays. The needle and the readouts move
  with the engine instead of a step behind it.
- "Black-box check" (Settings) also shows how many revs readings a second the car sends.

## Cluster Themes 0.26.4, HUD Widgets 0.18.3 — the speed reads like BMW's and holds still
- "Speed not matching the heads-up display; it flickers too fast" (Nov 22 2026). The HUD's speed is BMW's own, which
  over-reads on purpose; the car's speed signal is the true speed. New setting "Speed reads like BMW's speedometer
  (+%)", +3 % by default (0 = the true speed, up to +8 % in half steps) to line it up with the HUD.
- The number now moves the way BMW's does: the speed smoothed over 150 ms, the number changed at most 4 times a second
  and only once the speed is 0.6 past it, so it no longer flickers between two values. The speed needles use the same
  smoothed, calibrated speed. (HUD Widgets' own speed readouts too, at +3 %.)

## Cluster Themes 0.26.5, HUD Widgets 0.18.4 — shifts show at once, no overshoot
- "When I downshift there's a delay, and it's choppy" (Nov 22 2026). On a shift the revs now go straight to where the
  new gear puts them (the speed times that gear's revs per km/h, learned while driving in each gear, a ZF 8-speed
  330i's to start), held until the car's next reading arrives, instead of waiting a reading or two for the blip or drop.
- The carry-forward between readings only uses a rate two readings in a row agree on (the gentler of the two), and none
  for 400 ms after a shift, so a step (a shift, a blip) no longer overshoots and swings back.

## Cluster Themes 0.26.6, HUD Widgets 0.18.5 — the tach glides
- "Better, but going up and coming back down it's still choppy" (video Nov 22 2026). The needle used to land on each
  reading in 35 ms and wait for the next: stair steps. It now glides over about 0.7 of the gap between the car's
  readings (35..110 ms), and the carry-on runs that much further ahead so a steady climb or fall costs no lag.
  Simulated on readings every 100-200 ms with jitter: about half the frame-to-frame jerk of 0.26.5 at the same error.

## Cluster Themes 0.26.7 — M's map window
- M with the map in the theme (car photo Nov 22 2026): the window showed BMW's own map-screen speed readout cut off at
  its left edge, and BMW's map frame at its corners, in a hard rectangle. It now starts at x 716, past that readout,
  and fades in from the dash over 70 px with 60 px corners (new mdash "holeFeather").
