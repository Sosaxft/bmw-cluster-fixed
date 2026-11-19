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
