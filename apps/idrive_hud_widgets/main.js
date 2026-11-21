'use strict';
/**
 * HUD Widgets: custom widgets on the iDrive 7 windshield HUD, drawn through cluster-render.
 *
 * The center screen is the app's own page (shared/page.js, a canvas screen): the layouts with their
 * pictures, which drive mode shows which, and the settings. Each choice is saved in the app's data/settings.json
 * by the kit; the shared engine (hud.js) listens and redraws at once. It keeps running after the page is
 * closed (OAP apps stay up in the background), so the page is only needed for changes. The kit's own
 * settings list stays one tap away (the bar's All settings).
 */
const mgu = require('./kit/mgu');
const HudApp = require('./hud');
const Page = require('./page');
const { screenMux } = require('./screen_mux');

/**
 * Redline (cauliflowermossgrape/idrive7-apps apps/redline, MIT; redline/, with its own kit) runs in this same process:
 * its HUD (the G80 "Ramp" tach and the rest) shows where its settings say (Sport by default) and the widgets
 * everywhere else, as the two apps did side by side (kit hud_claim: the widgets step aside while Redline's tach holds
 * the HUD). Its centre-screen page is the other page of MAIN (screen_mux.js): the bar's Redline / Widgets button or
 * setting "centerPage". Its settings are the "Redline: ..." ones (tools/merge_redline.py).
 */
function startRedline(ctx) {
    try {
        const Redline = require('./redline/main.js');
        Promise.resolve(Redline.start(ctx)).catch((e) => ctx.log.error('Redline failed to start: ' + (e && e.stack || e)));
    } catch (e) {
        // the widgets go on without it: an exit here would count as a crash on the car
        ctx.log.error('Redline failed to load: ' + (e && e.stack || e));
    }
}

mgu.run({
    start(ctx) {
        let hud;
        try {
            hud = new HudApp(ctx);
        } catch (e) {
            // nothing drawn, but stay up: an exit here would count as a crash on the car
            ctx.log.error('HUD failed to start: ' + (e && e.stack || e));
            return;
        }
        hud.start();
        const first = ctx.settings.get('centerPage') === 'redline' ? 'redline' : 'widgets';
        const mux = screenMux(ctx, first);
        new Page(mux.view('widgets'), hud, {
            title: ctx.spec.title, what: 'HUD',
            look: { name: 'Layouts', style: 'cards', tags: { blinkers: 'arrows', daily: 'gear · clock · oil', sport: 'rev bar · temps · boost', redline: 'shift lights · shift score', minimal: 'round BMW speed', shiftonly: 'lights · gear', boost: 'boost · peak', warmup: 'oil · coolant · intake', track: 'lights · G-meter', cruise: 'range · trip', retro: 'amber digital', mview: 'rev band · km/h', vector: 'lights · now playing' } },
            tabs: ['look', 'readouts', 'position', 'colours', 'alerts', 'gmeter', 'settings'],
            settings: ['units', 'clock', 'timeZone', 'tankLitres', 'redline', 'shiftBefore', 'coldGuard', 'showTurn', 'turnWithRedline', 'showClock', 'showOil', 'showCoolant', 'showBoost', 'holiday', 'demo'],
            // the drive mode check's candidates this app's app.json listens to (issue #8; shared/hud.js modeDiagLines)
            modeCheck: ['HMI', 'MDrive', 'Sport2'],
        }).start();
        startRedline(mux.view('redline'));
        ['BTN_RESET', 'BTN_RESET_LEARNED', 'BTN_PAGE', 'BTN_PREV'].forEach((b) => { try { ctx.hideButton(b); } catch (e) { /* no kit bar */ } });
        const swap = () => { const to = mux.owner() === 'redline' ? 'widgets' : 'redline'; ctx.settings.set('centerPage', to); mux.show(to); };
        ctx.ui.onClick('BTN_SWAP', swap);
        ctx.settings.onChange((k) => { if (k === 'centerPage') mux.show(ctx.settings.get('centerPage') === 'redline' ? 'redline' : 'widgets'); });
        process.on('exit', () => { try { hud.stop(); } catch (e) { /* exiting anyway */ } });
    },
});
