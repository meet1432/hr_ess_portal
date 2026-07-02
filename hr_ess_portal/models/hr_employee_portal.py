# -*- coding: utf-8 -*-
"""
hr_employee_portal.py
=====================
Extends hr.employee with lightweight computed fields consumed by the
portal dashboard template.  No stored fields are added so no migration
is required when upgrading.

SECURITY NOTE
-------------
Never expose private salary data through public methods here.
All controller routes that call these fields are wrapped in
``http.route(auth='user')`` and backed by record rules that filter to
``employee_id.user_id = uid``.
"""

from odoo import models, fields, api


class HrEmployeePortal(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Computed helpers (non-stored → zero migration cost)
    # ------------------------------------------------------------------

    ess_leave_balance_ids = fields.One2many(
        'hr.leave.allocation',
        compute='_compute_ess_leave_balance_ids',
        string='Leave Balances',
        help='Virtual relation used in portal dashboard; not stored.',
    )

    ess_pending_leave_count = fields.Integer(
        compute='_compute_ess_pending_leave_count',
        string='Pending Leave Requests',
    )

    ess_last_check_in = fields.Datetime(
        compute='_compute_ess_last_check_in',
        string='Last Check-In',
    )

    ess_is_checked_in = fields.Boolean(
        compute='_compute_ess_is_checked_in',
        string='Currently Checked In',
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------

    @api.depends('user_id')
    def _compute_ess_leave_balance_ids(self):
        """Return validated allocations for this employee.
        Uses sudo() internally because portal users lack
        hr.leave.allocation read rights by default; the calling
        controller/template is responsible for scoping to self.
        """
        for emp in self:
            emp.ess_leave_balance_ids = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'validate'),
            ])

    @api.depends('user_id')
    def _compute_ess_pending_leave_count(self):
        for emp in self:
            emp.ess_pending_leave_count = self.env['hr.leave'].sudo().search_count([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['draft', 'confirm']),
            ])

    @api.depends('attendance_ids.check_in')
    def _compute_ess_last_check_in(self):
        Attendance = self.env['hr.attendance'].sudo()
        for emp in self:
            last = Attendance.search(
                [('employee_id', '=', emp.id)],
                order='check_in desc',
                limit=1,
            )
            emp.ess_last_check_in = last.check_in if last else False

    @api.depends('attendance_ids.check_out')
    def _compute_ess_is_checked_in(self):
        Attendance = self.env['hr.attendance'].sudo()
        for emp in self:
            open_att = Attendance.search([
                ('employee_id', '=', emp.id),
                ('check_out', '=', False),
            ], limit=1)
            emp.ess_is_checked_in = bool(open_att)
