# -*- coding: utf-8 -*-
"""
hr_timesheet_portal.py
======================
Adds safe portal-facing actions for timesheet entries.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class AccountAnalyticLinePortal(models.Model):
    _inherit = 'account.analytic.line'

    is_portal_entry = fields.Boolean(
        string='Portal Entry',
        default=False,
        help='Entry created from employee self-service portal'
    )

    is_submitted = fields.Boolean(
        string='Submitted for Approval',
        default=False,
        help='Timesheet submitted for approval'
    )

    def action_portal_submit(self, portal_user_id=None):
        """Submit timesheet entries from the portal for approval."""
        if portal_user_id and self.env.user.id != portal_user_id:
            _logger.warning('Timesheet submit failed: user mismatch')
            return {'success': False, 'error': 'Access denied.'}

        for entry in self:
            if entry.employee_id.user_id.id != self.env.user.id:
                return {'success': False, 'error': 'Cannot submit others\' timesheets.'}

        sp_name = f'ess_timesheet_submit_{self.id}'
        try:
            self.env.cr.execute(f'SAVEPOINT "{sp_name}"')
            # Validate timesheet entries
            for entry in self:
                if entry.unit_amount <= 0:
                    raise ValidationError(_('Hours must be greater than 0.'))
                if not entry.project_id and not entry.task_id:
                    raise ValidationError(_('Project or task is required.'))

            # Mark as submitted
            self.write({'is_submitted': True})
            self.env.cr.execute(f'RELEASE SAVEPOINT "{sp_name}"')
            _logger.info('Timesheet entries submitted: %s', self.ids)
            return {'success': True}
        except (ValidationError, UserError) as exc:
            self.env.cr.execute(f'ROLLBACK TO SAVEPOINT "{sp_name}"')
            _logger.warning('Timesheet submit failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    def action_portal_reject(self, portal_user_id=None):
        """Reject timesheet entries (for approval workflow)."""
        if portal_user_id and self.env.user.id != portal_user_id:
            return {'success': False, 'error': 'Access denied.'}

        if not self.env.user.has_group('hr.group_hr_user'):
            return {'success': False, 'error': 'Only HR users can reject timesheets.'}

        sp_name = f'ess_timesheet_reject_{self.id}'
        try:
            self.env.cr.execute(f'SAVEPOINT "{sp_name}"')
            self.write({'is_submitted': False})
            self.env.cr.execute(f'RELEASE SAVEPOINT "{sp_name}"')
            return {'success': True}
        except (ValidationError, UserError) as exc:
            self.env.cr.execute(f'ROLLBACK TO SAVEPOINT "{sp_name}"')
            return {'success': False, 'error': str(exc)}