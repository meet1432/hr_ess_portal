# -*- coding: utf-8 -*-
"""
hr_attendance_correction.py
===========================
Attendance correction request workflow.
Employees can request fixes for missed check-in/out via the portal.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAttendanceCorrection(models.Model):
    _name = 'hr.attendance.correction'
    _description = 'Attendance Correction Request'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    attendance_date = fields.Date('Date', required=True)
    correction_type = fields.Selection([
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out'),
        ('both', 'Both (Full Day)'),
    ], required=True)
    check_in_time = fields.Float('Check-in Time (HH:MM)', help='24-hour format, e.g., 9.5 = 9:30 AM')
    check_out_time = fields.Float('Check-out Time (HH:MM)', help='24-hour format, e.g., 17.75 = 5:45 PM')
    reason = fields.Text('Reason for Correction', required=True)
    state = fields.Selection([
        ('draft', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', readonly=True)
    rejection_reason = fields.Text('Rejection Reason')
    approver_id = fields.Many2one('res.users', readonly=True)

    @api.constrains('check_in_time', 'check_out_time')
    def _check_times(self):
        for rec in self:
            if rec.correction_type in ('check_in', 'both') and rec.check_in_time:
                if not (0 <= rec.check_in_time <= 24):
                    raise ValidationError('Check-in time must be between 0:00 and 23:59.')
            if rec.correction_type in ('check_out', 'both') and rec.check_out_time:
                if not (0 <= rec.check_out_time <= 24):
                    raise ValidationError('Check-out time must be between 0:00 and 23:59.')

    def action_approve(self):
        """Approve the correction and create/update attendance record."""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Only pending corrections can be approved.')

            from odoo.fields import Datetime
            from datetime import timedelta, datetime as dt_cls

            att_date = rec.attendance_date
            att_vals = {'employee_id': rec.employee_id.id}

            if rec.correction_type in ('check_in', 'both'):
                hours = int(rec.check_in_time)
                mins = int((rec.check_in_time % 1) * 60)
                check_in_dt = dt_cls.combine(att_date, dt_cls.min.time()).replace(hour=hours, minute=mins)
                att_vals['check_in'] = check_in_dt

            if rec.correction_type in ('check_out', 'both'):
                hours = int(rec.check_out_time)
                mins = int((rec.check_out_time % 1) * 60)
                check_out_dt = dt_cls.combine(att_date, dt_cls.min.time()).replace(hour=hours, minute=mins)
                att_vals['check_out'] = check_out_dt

            # Find or create attendance record for this date
            existing_att = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', f"{att_date} 00:00:00"),
                ('check_in', '<=', f"{att_date} 23:59:59"),
            ], limit=1)

            if existing_att:
                existing_att.write(att_vals)
            else:
                self.env['hr.attendance'].create(att_vals)

            rec.state = 'approved'
            rec.approver_id = self.env.user.id

    def action_reject(self, rejection_reason=''):
        """Reject the correction request."""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError('Only pending corrections can be rejected.')
            rec.state = 'rejected'
            rec.rejection_reason = rejection_reason
            rec.approver_id = self.env.user.id
