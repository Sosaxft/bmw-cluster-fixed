'use strict';
/**
 * One centre screen, two apps: HUD Widgets' page (page.js) and Redline's (redline/main.js) both draw the MAIN canvas
 * screen. Each gets a view of the kit's ctx (view(name)) that records what it registers on the screen (its loop, tab,
 * tap, scroll and layout handlers, its bar buttons); the real ctx gets one of each, which goes to the page on show
 * (owner). Pictures for MAIN from the page not on show are dropped. Everything else (settings, signals, the log, the
 * data folder, sheets) is the kit's own, shared.
 *
 *   const mux = screenMux(ctx, 'widgets');
 *   new Page(mux.view('widgets'), ...); Redline.start(mux.view('redline'));
 *   mux.show('redline')               the bar button BTN_SWAP and setting "centerPage" call this
 */
const { Recorder } = require('./kit/record');

const SCREEN = 'MAIN', PICTURE = 'MAIN_GFX', FPS = 15;

function screenMux(ctx, first) {
    let owner = first;
    const loops = {}, handlers = { tab: {}, tap: {}, scroll: {} }, clicks = {};
    let realLoop = null;
    const log = ctx.log;

    const kick = () => {
        const l = loops[owner];
        if (!l) return;
        try { const r = l(); if (r && r.catch) r.catch((e) => log.warn('screen ' + owner + ': ' + e)); } catch (e) { log.warn('screen ' + owner + ': ' + e); }
    };
    const relay = (kind) => (...a) => { const f = handlers[kind][owner]; return f ? f(...a) : null; };
    const realOn = {};
    const hook = (kind, method) => {
        if (realOn[kind] || typeof ctx[method] !== 'function') return;
        realOn[kind] = true;
        ctx[method](relay(kind));
    };

    function view(name) {
        const v = Object.create(ctx);
        const ui = Object.create(ctx.ui);
        ui.image = (n, cv) => (n === PICTURE && owner !== name ? Promise.resolve() : ctx.ui.image(n, cv));
        ui.onClick = (id, fn) => {
            if (!clicks[id]) {
                clicks[id] = {};
                ctx.ui.onClick(id, (...a) => { const f = clicks[id][owner]; return f ? f(...a) : null; });
            }
            clicks[id][name] = fn;
        };
        v.ui = ui;
        // the page not on show draws on a surface of its own, so it never resets the one on show mid-frame
        let spare = null;
        v.canvas = (w, h) => {
            if (owner === name) return ctx.canvas(w, h);
            if (!spare || spare.w !== w || spare.h !== h) spare = new Recorder(w, h, {});
            spare.reset();
            return spare;
        };
        v.loop = (screen, fps, fn) => {
            if (screen !== SCREEN) return ctx.loop(screen, fps, fn);
            loops[name] = fn;
            if (!realLoop) realLoop = ctx.loop(SCREEN, FPS, () => { const l = loops[owner]; return l ? l() : undefined; });
            return {
                stop() { delete loops[name]; },
                kick() { if (owner === name && realLoop && realLoop.kick) realLoop.kick(); },
            };
        };
        v.onTab = (fn) => { handlers.tab[name] = fn; hook('tab', 'onTab'); };
        v.onTap = (fn) => { handlers.tap[name] = fn; hook('tap', 'onTap'); };
        v.onScroll = (fn) => { handlers.scroll[name] = fn; hook('scroll', 'onScroll'); };
        // bar buttons: hidden once for both (the swap button and All settings stay)
        v.hideButton = (id) => { if (typeof ctx.hideButton === 'function') ctx.hideButton(id); };
        return v;
    }

    function show(name) {
        if (name === owner || !loops[name]) { owner = name; return; }
        owner = name;
        log.info('centre screen: ' + name);
        kick();
    }

    return { view, show, owner: () => owner };
}

module.exports = { screenMux };
