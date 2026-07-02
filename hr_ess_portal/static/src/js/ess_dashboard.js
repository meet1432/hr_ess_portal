/** @odoo-module **/
/**
 * ess_dashboard.js
 * ================
 * OWL 3 component for the ESS portal dashboard.
 *
 * Pattern notes
 * -------------
 * • Uses the Odoo 19 ``Interaction`` class pattern for progressive
 *   enhancement of server-rendered HTML (no full SPA takeover).
 * • JSON-RPC calls go through ``rpc`` from @web/core/network/rpc,
 *   which automatically injects the CSRF token from the session.
 *   Never hard-code session tokens or API keys here.
 * • Error messages are shown in the DOM; never surfaced to console
 *   in a way that leaks model structure.
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

// ── AttendanceClock ─────────────────────────────────────────────────
/**
 * Attaches to ``.js-attendance-clock`` and handles check-in / check-out
 * via JSON-RPC to the ESS portal controller.
 * The button text and dot colour update optimistically; on error the
 * previous state is restored.
 */
class AttendanceClock extends Interaction {
    static selector = ".js-attendance-clock";

    setup() {
        this.isCheckedIn = this.el.dataset.checkedIn === "1";
        this.btn = this.el.querySelector(".js-clock-btn");
        this.dot = this.el.querySelector(".js-clock-dot");
        this.statusText = this.el.querySelector(".js-clock-status");
        this.hoursEl = this.el.querySelector(".js-today-hours");
        this._updateUI();
        this.btn.addEventListener("click", () => this._toggle());
    }

    _updateUI() {
        if (this.isCheckedIn) {
            this.btn.textContent = "Check Out";
            this.dot.className = "ess-clock-dot ess-clock-dot--in";
            this.statusText.textContent = "Currently checked in";
        } else {
            this.btn.textContent = "Check In";
            this.dot.className = "ess-clock-dot ess-clock-dot--out";
            this.statusText.textContent = "Not checked in";
        }
    }

    async _toggle() {
        this.btn.disabled = true;
        const endpoint = this.isCheckedIn
            ? "/my/attendance/checkout"
            : "/my/attendance/checkin";
        try {
            const result = await rpc(endpoint, {});
            if (result.success) {
                this.isCheckedIn = !this.isCheckedIn;
                if (!this.isCheckedIn && result.worked_hours !== undefined) {
                    const current = parseFloat(this.hoursEl?.textContent || "0");
                    if (this.hoursEl) {
                        this.hoursEl.textContent = (
                            current + result.worked_hours
                        ).toFixed(2);
                    }
                }
                this._updateUI();
            } else {
                this._showError(result.error || "An error occurred.");
            }
        } catch (err) {
            this._showError("Network error. Please try again.");
        } finally {
            this.btn.disabled = false;
        }
    }

    _showError(msg) {
        const errEl = this.el.querySelector(".js-clock-error");
        if (errEl) {
            errEl.textContent = msg;
            errEl.style.display = "block";
            setTimeout(() => (errEl.style.display = "none"), 4000);
        }
    }
}

// ── LeaveQuickAction ────────────────────────────────────────────────
/**
 * Handles the inline "Request Leave" chip on the dashboard.
 * Shows / hides the mini-form without a full page reload.
 */
class LeaveQuickAction extends Interaction {
    static selector = ".js-leave-quick";

    setup() {
        this.trigger = this.el.querySelector(".js-leave-trigger");
        this.form = this.el.querySelector(".js-leave-form");
        this.cancelBtn = this.el.querySelector(".js-leave-cancel");
        if (this.trigger) {
            this.trigger.addEventListener("click", () => this._toggle(true));
        }
        if (this.cancelBtn) {
            this.cancelBtn.addEventListener("click", () => this._toggle(false));
        }
    }

    _toggle(open) {
        if (this.form) {
            this.form.style.display = open ? "block" : "none";
        }
        if (this.trigger) {
            this.trigger.style.display = open ? "none" : "flex";
        }
    }
}

// ── LiveClock ───────────────────────────────────────────────────────
/**
 * Renders a live HH:MM:SS clock in ``.js-live-clock`` elements.
 * The clock reads the user's local timezone from the browser; the
 * server is never queried for time (no unnecessary RPC).
 */
class LiveClock extends Interaction {
    static selector = ".js-live-clock";

    setup() {
        this._tick();
        this._interval = setInterval(() => this._tick(), 1000);
    }

    destroy() {
        clearInterval(this._interval);
    }

    _tick() {
        const now = new Date();
        this.el.textContent = now.toLocaleTimeString("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        });
    }
}

// ── FilterChips ─────────────────────────────────────────────────────
/**
 * Handles client-side chip selection for state filters on list pages.
 * Actual filtering is done server-side; chips update URL params and
 * re-submit the form (progressive enhancement).
 */
class FilterChips extends Interaction {
    static selector = ".js-filter-chips";

    setup() {
        this.chips = [...this.el.querySelectorAll(".ess-chip[data-filter]")];
        this.chips.forEach((chip) =>
            chip.addEventListener("click", () => this._activate(chip))
        );
    }

    _activate(selected) {
        this.chips.forEach((c) => c.classList.remove("ess-chip--active"));
        selected.classList.add("ess-chip--active");
        // Navigate with the filter param
        const url = new URL(window.location.href);
        url.searchParams.set("state_filter", selected.dataset.filter);
        url.searchParams.delete("page");
        window.location.href = url.toString();
    }
}

// ── Register all interactions ────────────────────────────────────────
const publicInteractionRegistry = registry.category("public.interactions");
publicInteractionRegistry.add("AttendanceClock", AttendanceClock);
publicInteractionRegistry.add("LeaveQuickAction", LeaveQuickAction);
publicInteractionRegistry.add("LiveClock", LiveClock);
publicInteractionRegistry.add("FilterChips", FilterChips);
