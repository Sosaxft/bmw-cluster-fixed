'use strict';
/**
 * The car's turn signals and hazard lights, for the HUD's arrows (hud.js widget type "turn").
 *
 * The body controller reports them on de.bmw.body.Light, StatusFunctionsIndicators / StatusFunctionsIndicators2
 * (subscribed; seen on a G05 by ZEKAI-Design/ID7-Cluster-Themes, Nov 2026): either the stalk's request
 * (controlIndicateDirection: TIPP_BLINKEN_LINKS_EIN 1 / 3, ..._RECHTS_EIN 2 / 4, BEIDSEITIGES_BLINKEN_EIN 8) or the
 * function running (activeFunctionIndicateDirection: DAUERBLINKEN_LINKS 7, TIPPBLINKEN_LINKS 9, ..._RECHTS 8 / 10,
 * WARNBLINKEN_MANUELL 6), BLINKEN_AUS / 0 for off; enums arrive as names or numbers, nested in the value.
 *
 * The car says which side is flashing, not when the lamp is lit, so the arrows flash on their own clock from the
 * moment the side started, at BMW's rate (about 1.5 Hz, lit half the time). Never throws.
 */

const PERIOD_MS = 680;
const STALK = {
    1: 'left', 3: 'left', TIPP_BLINKEN_LINKS_EIN: 'left', DAUER_BLINKEN_LINKS_EIN: 'left',
    2: 'right', 4: 'right', TIPP_BLINKEN_RECHTS_EIN: 'right', DAUER_BLINKEN_RECHTS_EIN: 'right',
    8: 'both', BEIDSEITIGES_BLINKEN_EIN: 'both',
};
const ACTIVE = {
    7: 'left', 9: 'left', DAUERBLINKEN_LINKS: 'left', TIPPBLINKEN_LINKS: 'left',
    8: 'right', 10: 'right', DAUERBLINKEN_RECHTS: 'right', TIPPBLINKEN_RECHTS: 'right',
    6: 'both', WARNBLINKEN_MANUELL: 'both', WARNBLINKEN_AUTOMATISCH: 'both',
};
const OFF = { 0: true, BLINKEN_AUS: true };

/** the object holding key, anywhere in v (the car nests its struct one or two levels down), or null */
function holder(v, key, depth) {
    if (!v || typeof v !== 'object' || (depth || 0) > 4) return null;
    if (Object.prototype.hasOwnProperty.call(v, key)) return v;
    for (const k of Object.keys(v)) {
        const f = holder(v[k], key, (depth || 0) + 1);
        if (f) return f;
    }
    return null;
}

const pick = (table, v) => (Object.prototype.hasOwnProperty.call(table, v) ? table[v] : null);

class TurnSignal {
    constructor(log) {
        this.log = log || null;
        this.side = 'off';     // 'off', 'left', 'right', 'both'
        this.since = 0;
    }

    /** a StatusFunctionsIndicators(2) value */
    feed(v) {
        try {
            const s = holder(v, 'activeFunctionIndicateDirection') || holder(v, 'controlIndicateDirection');
            if (!s) return;
            const active = s.activeFunctionIndicateDirection, stalk = s.controlIndicateDirection;
            const side = pick(ACTIVE, active) || pick(STALK, stalk);
            if (side) this._set(side);
            else if (pick(OFF, active) || (active === undefined && pick(OFF, stalk))) this._set('off');
        } catch (e) { /* a value of a shape we don't know: keep what we had */ }
    }

    /** the signal went away (the interface isn't there, or was lost) */
    reset() { this._set('off'); }

    _set(side) {
        if (side === this.side) return;
        this.side = side;
        this.since = Date.now();
        if (this.log) this.log.info('turn signal: ' + side);
    }

    /** [left lit, right lit] as 0 / 1 at now (ms), flashing */
    lit(now) {
        if (this.side === 'off') return [0, 0];
        const on = ((now - this.since) % PERIOD_MS + PERIOD_MS) % PERIOD_MS < PERIOD_MS / 2 ? 1 : 0;
        return [this.side !== 'right' ? on : 0, this.side !== 'left' ? on : 0];
    }
}

module.exports = { TurnSignal, PERIOD_MS };
