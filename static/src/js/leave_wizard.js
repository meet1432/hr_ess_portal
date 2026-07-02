/** @odoo-module **/
/**
 * leave_wizard.js
 * ===============
 * Client-side enhancements for the leave request form:
 *  • Dynamic day-count calculation between date_from / date_to
 *  • Prevents submitting dates in the past (client hint; server validates)
 *  • Shows leave balance for the selected leave type
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

class LeaveWizard extends Interaction {
    static selector = ".js-leave-wizard";

    setup() {
        this.form = this.el;
        this.dateFrom = this.el.querySelector('[name="date_from"]');
        this.dateTo = this.el.querySelector('[name="date_to"]');
        this.dayCount = this.el.querySelector(".js-day-count");
        this.balanceHint = this.el.querySelector(".js-balance-hint");
        this.leaveTypeSelect = this.el.querySelector('[name="leave_type_id"]');

        if (this.dateFrom && this.dateTo) {
            this.dateFrom.addEventListener("change", () => this._updateDays());
            this.dateTo.addEventListener("change", () => this._updateDays());
        }
        if (this.leaveTypeSelect) {
            this.leaveTypeSelect.addEventListener("change", () =>
                this._updateBalance()
            );
        }
    }

    _updateDays() {
        const from = new Date(this.dateFrom.value);
        const to = new Date(this.dateTo.value);
        if (!isNaN(from) && !isNaN(to) && to >= from) {
            const diff = Math.ceil((to - from) / (1000 * 60 * 60 * 24)) + 1;
            if (this.dayCount) {
                this.dayCount.textContent = `${diff} day${diff !== 1 ? "s" : ""}`;
            }
            // Warn if date_from is in the past
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const warn = this.el.querySelector(".js-past-warn");
            if (warn) {
                warn.style.display = from < today ? "block" : "none";
            }
        }
    }

    _updateBalance() {
        const selected = this.leaveTypeSelect.selectedOptions[0];
        if (selected && this.balanceHint) {
            const balance = selected.dataset.balance || "—";
            this.balanceHint.textContent = `Available: ${balance} days`;
        }
    }
}

registry
    .category("public.interactions")
    .add("LeaveWizard", LeaveWizard);
