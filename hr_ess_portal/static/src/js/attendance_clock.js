/** @odoo-module **/
/**
 * attendance_clock.js
 * ===================
 * Standalone timer that shows elapsed time for the current check-in session.
 * Reads check-in timestamp from a data attribute; no API call on tick.
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

class AttendanceTimer extends Interaction {
    static selector = ".js-attendance-timer";

    setup() {
        const checkInIso = this.el.dataset.checkIn;
        if (!checkInIso) return;
        this._checkInTime = new Date(checkInIso);
        this._tick();
        this._interval = setInterval(() => this._tick(), 1000);
    }

    destroy() {
        clearInterval(this._interval);
    }

    _tick() {
        const elapsed = Math.floor((Date.now() - this._checkInTime) / 1000);
        const h = String(Math.floor(elapsed / 3600)).padStart(2, "0");
        const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0");
        const s = String(elapsed % 60).padStart(2, "0");
        this.el.textContent = `${h}:${m}:${s}`;
    }
}

registry
    .category("public.interactions")
    .add("AttendanceTimer", AttendanceTimer);
