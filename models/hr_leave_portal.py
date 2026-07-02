# -*- coding: utf-8 -*-
"""
hr_leave_portal.py
==================
Adds safe portal-facing actions for leave requests.

Pattern
-------
Each public method uses a manual SAVEPOINT so a validation failure inside
Odoo's action_confirm() never partially commits.  The controller calls
these via JSON-RPC and renders the error message in-template.
"""

from odoo import models, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class HrLeavePortal(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        """
        This method is overridden to handle approvals of leave requests
        created by portal users. The original method fails because it
        tries to schedule an activity as the portal user, who lacks the
        necessary permissions.

        The fix is to call activity_update() with sudo() to ensure it runs
        with elevated privileges, while the rest of the approval logic
        runs as the logged-in administrator.
        """
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only HR Officers can approve leave requests.'))

        # if validation is handled by models, check if all records are in confirm state
        if self.filtered(lambda holiday: holiday.state not in ['confirm', 'validate1']):
            raise UserError(_('Leave request must be confirmed ("To Approve") or "Second Approval" in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.state == 'validate1').write({'state': 'validate'})
        self.filtered(lambda hol: hol.validation_type == 'both' and hol.state == 'confirm').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: not hol.validation_type == 'both' and hol.state == 'confirm').write({'state': 'validate'})
        if not self.env.context.get('leave_fast_create'):
            self.sudo().activity_update()
        return True

    # ------------------------------------------------------------------
    # Portal actions (called from controllers/portal.py)
    # ------------------------------------------------------------------

    def action_portal_submit(self, portal_user_id=None):
        """Submit a leave request from the portal.

        The caller (controller) is expected to have already verified
        ownership via domain filters.  An optional *portal_user_id*
        can be passed for an extra safety check.

        The method runs on a **sudo** recordset so mail-tracking and
        activity-scheduling have the privileges they need.

        Returns a dict so the controller can relay the outcome
        as JSON without raising an HTTP error page.
        """
        self.ensure_one()
        # Optional secondary guard: caller may pass the real portal uid
        if portal_user_id and self.employee_id.user_id.id != portal_user_id:
            _logger.warning('ESS leave submit failed for leave %s: portal user mismatch', self.id)
            return {'success': False, 'error': 'Access denied.'}

        sp_name = f'ess_leave_submit_{self.id}'
        try:
            self.env.cr.execute(f'SAVEPOINT "{sp_name}"')
            if self.state == 'draft':
                self.action_confirm()
                # Re-browse to ensure the state change is reflected
                self.browse(self.id)
            self.env.cr.execute(f'RELEASE SAVEPOINT "{sp_name}"')
            _logger.info('ESS leave %s submitted successfully', self.id)
            return {'success': True}
        except (ValidationError, UserError) as exc:
            self.env.cr.execute(f'ROLLBACK TO SAVEPOINT "{sp_name}"')
            _logger.warning('ESS leave submit failed for leave %s: %s', self.id, exc)
            return {'success': False, 'error': str(exc)}

    def action_portal_cancel(self, portal_user_id=None):
        """Cancel a pending leave from the portal.

        Same sudo pattern as action_portal_submit.
        """
        self.ensure_one()
        if portal_user_id and self.employee_id.user_id.id != portal_user_id:
            return {'success': False, 'error': 'Access denied.'}
        if self.state not in ('draft', 'confirm'):
            return {'success': False, 'error': 'Only pending leaves can be cancelled.'}

        sp_name = f'ess_leave_cancel_{self.id}'
        try:
            self.env.cr.execute(f'SAVEPOINT "{sp_name}"')
            self._force_cancel()
            self.env.cr.execute(f'RELEASE SAVEPOINT "{sp_name}"')
            return {'success': True}
        except (ValidationError, UserError) as exc:
            self.env.cr.execute(f'ROLLBACK TO SAVEPOINT "{sp_name}"')
            return {'success': False, 'error': str(exc)}
