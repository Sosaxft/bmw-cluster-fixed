'use strict';
/**
 * waze.js - "Show Waze map inside the theme" (Cluster Themes, page.js Map tab).
 *
 * robertnisipeanu's waze-on-cluster draws the phone's map on cluster-render's "map" target by default: the KOMBI
 * slot UNDER BMW's gauges, so BMW's own map-view readouts (speed, consumption, badge) always sit over it and a
 * see-through hole in a theme shows them too. Nothing can hide that overlay. Its other target, "panel", puts
 * the map inside the panel scene our theme draws on, ABOVE BMW's gauges: our frame is drawn over it with a
 * rounded window, our readouts over that, BMW's overlay under all of it.
 *
 * What this does (and nothing else):
 *  - reads waze-on-cluster's status file (/run/waze-on-cluster/status.json, 0644, rewritten about once a second:
 *    { state: idle|starting|showing|frozen|error|off|unsupported, target, ... }) every second;
 *  - while wanted (the setting is on and the theme has a map layout) and the map isn't on "panel": connects to
 *    its control socket (/dev/shm/waze-on-cluster/ctl.sock, group tm_oap_app), writes {"cmd":"start","target":
 *    "panel"}, and closes again within a second. The socket has one owner: the Waze app holds it while its page
 *    is open and a second connection is told "busy" and closed, so we never hold it and retry every 5 s;
 *  - when no longer wanted, and only if WE moved it, sends "start map" once so Waze is back where it was (the
 *    panel shares its scene with the HUD, so leaving it there would block HUD Widgets and Waze's HUD map).
 * "start" isn't saved by waze-on-cluster (a restart of its service puts it back on "map"); we just send it again.
 * Never sent: "cluster" (would turn the map off), "guide" (saved by the tool). Never touched: patch.sock (root).
 * Facts from the waze-on-cluster 0.9.3 source (main.cpp, control.cpp, map_feed.cpp, the .socket unit), read
 * Nov 7 2026. Plain Node 8 (the car's 8.16.2).
 *
 * Maps on cluster 0.11 (waze-on-cluster 0.11.0, Nov 20 2026; main.cpp, map_feed.cpp, control.cpp read Nov 21) has no
 * "start" command and no "panel" target any more: the map always goes on the cluster's own map slot ("map", 1088x480
 * at 416,120 of the panel, under BMW's gauges), where the theme's see-through window shows it, exactly as BMW's own
 * Map view would. Its status line says so with a "cluster" field (1: Show on includes the cluster). With that field
 * this sends nothing: the map is up while state is "showing", target "map" and cluster 1. (Hosting it in our own scene
 * instead needs a RAMSES scene file, off on every car as cluster-render ships.)
 *
 * The layout window (eroobeeroo's Waze on Cluster 0.9.107+, layout_window.h; ZEKAI's ID7 Cluster Themes uses it too):
 * a theme that writes /dev/shm/cluster-info/map_window.txt, one line "panel X Y W H", and keeps it fresh (touched at
 * least every 3 s) gets the map drawn on the panel itself in that rect, ABOVE the theme. In the map slot under a theme
 * the KOMBI draws its own map screen over the map (its speed readout, shading, and with BimmerCode's M display dark
 * boxes): over the theme none of that shows. The file is a lease: made with O_EXCL, taken over from another app only
 * when stale (5 s, ZEKAI's rule), removed when we stop wanting it. Harmless where the map app doesn't read it.
 */
const fs = require('fs');
const net = require('net');
const path = require('path');

const STATUS_PATH = '/run/waze-on-cluster/status.json';
const CONTROL_PATH = '/dev/shm/waze-on-cluster/ctl.sock';
const POLL_MS = 1000;
const STALE_MS = 10000;          // a status file older than this: the service isn't running
const RETRY_MS = 5000;           // between two sends (busy, error, or waiting for the status to show the switch)
const LINGER_MS = 800;           // how long we stay connected after the command (its answer, then close)

const WINDOW_PATH = '/dev/shm/cluster-info/map_window.txt';
const WINDOW_STALE_MS = 5000;     // another app's window file older than this is taken over

class Waze {
    /**
     * opts: { status, control, dataDir }; env WAZE_STATUS / WAZE_CTL override the paths (the Mac bench's fake).
     * onChange(): called when "up" (the map is showing inside the theme) or the page's status text changes.
     */
    constructor(opts, log, onChange) {
        opts = opts || {};
        this.statusPath = process.env.WAZE_STATUS || opts.status || STATUS_PATH;
        this.controlPath = process.env.WAZE_CTL || opts.control || CONTROL_PATH;
        this.memo = opts.dataDir ? path.join(opts.dataDir, 'waze.json') : null;
        this.log = log;
        this.onChange = onChange || (() => {});
        this.wanted = false;
        this.st = null;              // the last status read: { state, target } or null (no file / unreadable / stale)
        this.up = false;             // the map is showing on the panel
        this.over = false;           // ... drawn over the theme, in our layout window
        this.sending = false;
        this.nextTry = 0;
        this.problem = null;         // 'busy' | an error text, from the last send
        this.moved = false;          // we put it on the panel (so we put it back)
        try { this.moved = JSON.parse(fs.readFileSync(this.memo, 'utf8')).moved === true; } catch (e) { /* first run */ }
        this.lastText = null;
        this.windowPath = process.env.WAZE_WINDOW || opts.window || WINDOW_PATH;
        this.window = null;          // the theme's window for the map, [x, y, w, h] on the panel, or null
        this.windowFd = null;        // our lease on the window file
        this.windowLine = null;
        this.windowWarned = false;
    }

    /** The active theme's window for the map on the panel ([x, y, w, h]), or null: written as the layout window. */
    setWindow(rect) {
        const line = rect ? 'panel ' + rect.map((v) => Math.round(v)).join(' ') : null;
        if (line === this.windowLine) return;
        this._release();
        this.window = rect || null;
        this.windowLine = line;
        this._lease();
    }

    /** Hold (and touch) the window file while the map is wanted and the theme has a window; else let it go. */
    _lease() {
        if (!this.wanted || !this.windowLine) return this._release();
        try {
            if (this.windowFd === null) {
                const dir = path.dirname(this.windowPath);
                try { fs.mkdirSync(dir, 0o1777); fs.chmodSync(dir, 0o1777); } catch (e) { if (e.code !== 'EEXIST') throw e; }
                try {
                    this.windowFd = fs.openSync(this.windowPath, 'wx', 0o644);
                } catch (e) {
                    if (e.code !== 'EEXIST') throw e;
                    const st = fs.lstatSync(this.windowPath);
                    if (!st.isFile() || Date.now() - st.mtimeMs < WINDOW_STALE_MS) { this.windowHeldBy = 'another app'; return; }
                    fs.unlinkSync(this.windowPath);
                    this.windowFd = fs.openSync(this.windowPath, 'wx', 0o644);
                }
                fs.writeSync(this.windowFd, this.windowLine + '\n');
                try { fs.fchmodSync(this.windowFd, 0o644); } catch (e) { /* best effort */ }
                this.windowHeldBy = null;
                this.log.info('waze: map window ' + this.windowLine);
            }
            const now = new Date();
            fs.futimesSync(this.windowFd, now, now);
        } catch (e) {
            if (!this.windowWarned) { this.windowWarned = true; this.log.warn('waze: map window file: ' + e.message); }
            this._release();
        }
    }

    _release() {
        if (this.windowFd === null) return;
        try { fs.closeSync(this.windowFd); } catch (e) { /* closed */ }
        this.windowFd = null;
        try { fs.unlinkSync(this.windowPath); } catch (e) { /* gone */ }
    }

    start() {
        this.timer = setInterval(() => this._poll(), POLL_MS);
        this._poll();
    }

    /** Stop polling; if we moved the map, ask once for it back on "map" (best effort: the process may be exiting). */
    stop() {
        clearInterval(this.timer);
        this._release();
        if (this.moved && this.st && this.st.target === 'panel') this._send('map');
    }

    /** Whether the theme wants the map on the panel now (the setting, and a layout with a map window). */
    want(on) {
        on = on === true;
        if (on === this.wanted) return;
        this.wanted = on;
        this.nextTry = 0;
        this._lease();
        this._sync();
    }

    /** For the page: { text, up, ok } (ok: false when something is wrong). */
    info() {
        const s = this.st;
        if (!s) return { text: 'Waze on Cluster isn\'t running', up: false, ok: false };
        if (s.state === 'unsupported') return { text: 'Waze on Cluster: this car isn\'t supported', up: false, ok: false };
        if (s.state === 'off') return { text: 'Waze map is turned off in the Waze app', up: false, ok: false };
        if (!this.wanted) return { text: 'Off. Waze shows the map in BMW\'s own map view', up: false, ok: true };
        if (this.windowFd !== null && s.target === 'panel' && s.state === 'showing') return { text: 'Map showing over the theme', up: true, ok: true };
        if (s.v11) {
            // Maps on cluster 0.11+: the map on the cluster's own map slot, seen through the theme's window
            if (!s.cluster) return { text: 'Maps on cluster: set Show on to Cluster', up: false, ok: false };
            if (s.state === 'showing') return { text: 'Map showing in the theme (under BMW\'s map screen)', up: true, ok: true };
            if (s.state === 'frozen') return { text: 'Map frozen, waiting for the phone', up: false, ok: false };
            if (s.state === 'error') return { text: 'Maps on cluster reports an error', up: false, ok: false };
            return { text: 'Waiting for the phone\'s map (Central display area: Map view)', up: false, ok: true };
        }
        if (s.target !== 'panel') {
            if (this.problem === 'busy') return { text: 'Waze app is open, retrying', up: false, ok: false };
            if (this.problem) return { text: 'Can\'t reach Waze on Cluster (' + this.problem + ')', up: false, ok: false };
            return { text: 'Moving the map into the theme', up: false, ok: true };
        }
        if (s.state === 'showing') return { text: 'Map showing in the theme', up: true, ok: true };
        if (s.state === 'frozen') return { text: 'Map frozen, waiting for the phone', up: false, ok: false };
        if (s.state === 'error') return { text: 'Waze on Cluster reports an error', up: false, ok: false };
        return { text: 'Waiting for the map', up: false, ok: true };
    }

    _poll() {
        this._lease();
        fs.stat(this.statusPath, (err, st) => {
            if (err || Date.now() - st.mtime.getTime() > STALE_MS) return this._update(null);
            fs.readFile(this.statusPath, 'utf8', (e, txt) => {
                let s = null;
                try { if (!e) { const j = JSON.parse(txt); s = { state: String(j.state || ''), target: j.target == null ? null : String(j.target), v11: 'cluster' in j, cluster: j.cluster !== 0 && j.cluster !== '0' }; } } catch (x) { s = null; }
                this._update(s);
            });
        });
    }

    _update(s) {
        this.st = s;
        if (s && s.target === 'map' && this.moved && (!this.wanted || s.v11)) this._setMoved(false);   // it's back (0.11: always)
        if (s && s.target === 'panel' && this.problem) this.problem = null;
        const up = !!(this.wanted && s && s.state === 'showing' && (s.v11 ? s.cluster && (s.target === 'map' || s.target === 'panel') : s.target === 'panel'));
        // over: drawn on the panel over the theme, in the window we hold (a map app that reads it)
        const over = !!(up && this.windowFd !== null && s.target === 'panel');
        const text = this.info().text;
        const changed = up !== this.up || over !== this.over || text !== this.lastText;
        this.up = up;
        this.over = over;
        this.lastText = text;
        this._sync();
        if (changed) this.onChange();
    }

    _sync() {
        const s = this.st;
        if (this.sending || Date.now() < this.nextTry || !s) return;
        if (s.state === 'unsupported' || s.state === 'off' || s.v11) return;   // 0.11+: nothing to ask for
        if (this.windowFd !== null) return;      // the layout window moves it (a map app that reads it)
        if (this.wanted && s.target !== 'panel') this._send('panel');
        else if (!this.wanted && this.moved && s.target === 'panel') this._send('map');
    }

    _send(target) {
        this.sending = true;
        this.nextTry = Date.now() + RETRY_MS;
        let answer = '', done = false;
        const sock = net.connect(this.controlPath);
        const finish = (problem) => {
            if (done) return;
            done = true;
            clearTimeout(t);
            try { sock.destroy(); } catch (e) { /* closed */ }
            this.sending = false;
            if (/"reason"\s*:\s*"busy"/.test(answer)) problem = 'busy';
            this.problem = problem || null;
            if (!this.problem) {
                this.log.info('waze: asked for the map on "' + target + '"');
                if (target === 'panel') this._setMoved(true);
            } else this.log.info('waze: "start ' + target + '" not sent (' + this.problem + '), retrying in ' + RETRY_MS / 1000 + ' s');
        };
        const t = setTimeout(() => finish(null), LINGER_MS + 1000);
        sock.setEncoding('utf8');
        sock.on('data', (d) => { if (answer.length < 4096) answer += d; });
        sock.on('error', (e) => finish(e.code || e.message));
        sock.on('close', () => finish(null));
        sock.on('connect', () => {
            sock.write(JSON.stringify({ cmd: 'start', target }) + '\n');
            setTimeout(() => { try { sock.end(); } catch (e) { /* closed */ } }, LINGER_MS);
        });
    }

    _setMoved(on) {
        this.moved = on;
        if (!this.memo) return;
        try { fs.writeFileSync(this.memo, JSON.stringify({ moved: on })); } catch (e) { this.log.warn('waze: cannot save ' + this.memo + ' (' + e.message + ')'); }
    }
}

module.exports = Waze;
