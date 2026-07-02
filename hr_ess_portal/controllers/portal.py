# -*- coding: utf-8 -*-
"""
controllers/portal.py
=====================
All ESS Portal HTTP routes.

Security model
--------------
1. Every route uses ``auth='user'``.  Unauthenticated requests are
   redirected to /web/login by Odoo's base portal mixin.
2. ``_get_employee_or_403`` raises NotFound (→ HTTP 404) if the logged-in
   portal user has no linked employee, preventing information leakage.
3. Record-rule enforcement happens at the ORM level automatically;
   controllers never build domain filters manually for security —
   they rely entirely on the rules in security/hr_ess_portal_rules.xml.

NEVER put API keys, tokens, or secrets in controller code.
"""

from calendar import monthrange, monthcalendar
from datetime import date
from urllib.parse import urlencode

from odoo import fields, http
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging

_logger = logging.getLogger(__name__)

_ITEMS_PER_PAGE = 20


class EssPortalController(CustomerPortal):
    """Extends the base CustomerPortal to add ESS sections."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_is_portal_user_or_redirect(self):
        """
        Checks if the current user is an internal user (not a portal user).
        If so, returns a redirect to the backend. Otherwise, returns None.
        This prevents internal users from accessing portal pages.
        """
        if request.env.user.has_group('base.group_user'):
            return request.redirect('/web')
        return None

    def _get_employee_or_404(self):
        """Return the hr.employee for the current user or None."""
        return request.env['hr.employee'].search(
            [('user_id', '=', request.env.user.id)],
            limit=1,
        )

    def _ess_base_values(self, employee, page_name):
        """Common template values injected into every ESS page."""
        employee_sudo = employee.sudo()
        company = employee_sudo.company_id
        job = employee_sudo.job_id
        department = employee_sudo.department_id

        # Company logo URL - try multiple field names
        company_logo_url = ''
        if company:
            # Try logo_1920 first (standard in Odoo 19)
            if hasattr(company, 'logo_1920') and company.logo_1920:
                company_logo_url = f'/web/image/res.company/{company.id}/logo_1920'
            # Fallback to logo field
            elif hasattr(company, 'logo') and company.logo:
                company_logo_url = f'/web/image/res.company/{company.id}/logo'
            # Fallback to image_1920 (some versions)
            elif hasattr(company, 'image_1920') and company.image_1920:
                company_logo_url = f'/web/image/res.company/{company.id}/image_1920'

        return {
            'employee_name': employee_sudo.name or '',
            'employee_initials': (employee_sudo.name or 'U')[:2].upper(),
            'employee_company_name': company.name or 'ESS Portal',
            'employee_company_logo': company_logo_url,
            'employee_job_title': job.name or employee_sudo.job_title or '',
            'employee_department_name': department.name or '',
            'employee_work_email': employee_sudo.work_email or '',
            'employee_last_check_in': employee_sudo.ess_last_check_in,
            'employee_pending_leave_count': employee_sudo.ess_pending_leave_count,
            'employee_is_checked_in': employee_sudo.ess_is_checked_in,
            'page_name': page_name,
        }

    def _month_bounds(self, month_filter):
        """Return the first and last day for a YYYY-MM filter."""
        if not month_filter:
            return None, None
        year, month = (int(part) for part in month_filter.split('-'))
        last_day = monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)

    def _leave_type_domain(self, employee):
        """Leave types visible to the current employee in the portal."""
        company_id = employee.company_id.id
        return [
            ('active', '=', True),
            ('employee_requests', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company_id),
            '|',
            ('requires_allocation', '=', False),
            ('has_valid_allocation', '=', True),
        ]

    # ------------------------------------------------------------------
    # Portal home – add ESS tile
    # ------------------------------------------------------------------

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        employee = self._get_employee_or_404()
        if employee and 'ess_leave_count' in counters:
            values['ess_leave_count'] = request.env['hr.leave'].sudo().search_count([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['draft', 'confirm', 'validate1', 'validate']),
            ])
        return values

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    @http.route('/my/dashboard', type='http', auth='user')
    def ess_dashboard(self, **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        # Payslip KPI (latest 3)
        payslips = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['done', 'paid', 'validate']),
        ], order='date_to desc', limit=3)

        # Leave balances
        allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
        ])

        # Attendance – today and this week
        today_date = date.today()
        today_start = f"{today_date} 00:00:00"
        today_end = f"{today_date} 23:59:59"

        # Week start (Monday)
        from datetime import timedelta
        week_start = today_date - timedelta(days=today_date.weekday())
        week_start_str = f"{week_start} 00:00:00"
        week_end_str = f"{today_date} 23:59:59"

        today_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
        ])
        today_hours = sum(today_att.mapped('worked_hours'))
        today_records = len(today_att)

        week_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', week_start_str),
            ('check_in', '<=', week_end_str),
        ])
        week_hours = sum(week_att.mapped('worked_hours'))
        week_records = len(week_att)

        # Expense overview – pending vs submitted
        pending_expenses = 0
        pending_expense_sheets = 0
        try:
            pending_expenses = request.env['hr.expense'].sudo().search_count([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['draft', 'reported']),
            ])
        except:
            pass

        try:
            pending_expense_sheets = request.env['hr.expense.sheet'].sudo().search_count([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['draft', 'submit']),
            ])
        except:
            pass

        # Tasks (if project module is installed)
        tasks = []
        try:
            tasks = request.env['project.task'].sudo().search([
                ('user_ids', 'in', request.env.user.id),
                ('stage_id.fold', '=', False),  # Exclude completed stages
            ], order='date_deadline asc', limit=5)
        except:
            pass

        # Timesheets (if timesheet module is installed)
        timesheets_today = []
        timesheets_week = []
        try:
            timesheets_today = request.env['account.analytic.line'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date', '=', today_date),
            ])
            timesheets_week = request.env['account.analytic.line'].sudo().search([
                ('employee_id', '=', employee.id),
                ('date', '>=', week_start),
                ('date', '<=', today_date),
            ])
        except:
            pass

        today_timesheet_hours = sum(timesheets_today.mapped('unit_amount')) if timesheets_today else 0
        week_timesheet_hours = sum(timesheets_week.mapped('unit_amount')) if timesheets_week else 0

        # Leave request status breakdown
        leave_pending = request.env['hr.leave'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'confirm'),
        ])
        leave_approved = request.env['hr.leave'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate1'),
            ('date_from', '>=', f"{today_date}"),
        ])
        leave_rejected = request.env['hr.leave'].sudo().search_count([
            ('employee_id', '=', employee.id),
            ('state', '=', 'refuse'),
        ])

        # Upcoming leaves (next 5)
        upcoming_leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate1'),
            ('date_from', '>=', f"{today_date}"),
        ], order='date_from asc', limit=5)

        # Active projects
        active_projects = []
        total_active_projects = 0
        try:
            active_projects = request.env['project.project'].sudo().search([
                ('active', '=', True),
                ('allow_timesheets', '=', True),
            ], order='name asc', limit=3)
            total_active_projects = request.env['project.project'].sudo().search_count([
                ('active', '=', True),
                ('allow_timesheets', '=', True),
            ])
        except:
            pass

        # Total tasks count
        total_tasks = len(tasks)

        # Attendance status (target is 8 hours per day)
        target_hours_per_day = 8.0
        attendance_status = 'on-track'
        if today_hours > target_hours_per_day * 1.1:
            attendance_status = 'overtime'
        elif today_hours < target_hours_per_day * 0.75:
            attendance_status = 'behind'

        values = {
            **self._ess_base_values(employee, 'dashboard'),
            'payslips': payslips,
            'allocations': allocations,
            'today_hours': round(float(today_hours), 2),
            'week_hours': round(float(week_hours), 2),
            'today_records': today_records,
            'week_records': week_records,
            'pending_expenses': pending_expenses,
            'pending_requests': pending_expense_sheets,
            'tasks': tasks,
            'total_tasks': total_tasks,
            'timesheets_today': round(float(today_timesheet_hours), 2),
            'timesheets_week': round(float(week_timesheet_hours), 2),
            'leave_pending': leave_pending,
            'leave_approved': leave_approved,
            'leave_rejected': leave_rejected,
            'upcoming_leaves': upcoming_leaves,
            'active_projects': active_projects,
            'total_active_projects': total_active_projects,
            'attendance_status': attendance_status,
            'target_hours_per_day': target_hours_per_day,
        }
        return request.render('hr_ess_portal.portal_dashboard', values)

    # ------------------------------------------------------------------
    # Leave – list + create
    # ------------------------------------------------------------------

    @http.route(['/my/leaves', '/my/leaves/page/<int:page>'], type='http', auth='user')
    def ess_leaves(self, page=1, state_filter='all', **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()
        # Build domain with filters from the UI (search, date range)
        domain = [('employee_id', '=', employee.id)]
        if state_filter != 'all':
            domain.append(('state', '=', state_filter))

        # Optional filters
        q = (kwargs.get('q') or '').strip()
        date_from = kwargs.get('date_from', '').strip()
        date_to = kwargs.get('date_to', '').strip()
        grouping = kwargs.get('grouping', 'none')

        if q:
            # search by leave type name or description
            domain += ['|', ('holiday_status_id.name', 'ilike', q), ('name', 'ilike', q)]

        if date_from:
            try:
                domain.append(('date_from', '>=', date_from))
            except Exception:
                pass

        if date_to:
            try:
                domain.append(('date_to', '<=', date_to))
            except Exception:
                pass

        Leave = request.env['hr.leave'].sudo()
        total = Leave.search_count(domain)
        pager = portal_pager(
            url='/my/leaves',
            total=total,
            page=page,
            step=_ITEMS_PER_PAGE,
            url_args={'state_filter': state_filter, 'q': q, 'date_from': date_from, 'date_to': date_to, 'grouping': grouping},
        )
        leaves = Leave.search(
            domain, order='date_from desc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )
        leave_types = request.env['hr.leave.type'].sudo().with_context(
            employee_id=employee.id,
            default_employee_id=employee.id,
        ).search(self._leave_type_domain(employee))
        
        allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
        ])

        values = {
            **self._ess_base_values(employee, 'leaves'),
            'leaves': leaves,
            'pager': pager,
            'leave_types': leave_types,
            'allocations': allocations,
            'state_filter': state_filter,
            'q': q,
            'date_from': date_from,
            'date_to': date_to,
            'grouping': grouping,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_leaves', values)

    @http.route('/my/leaves/new', type='http', auth='user', methods=['GET'])
    def ess_leave_new(self, **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()
        leave_types = request.env['hr.leave.type'].sudo().with_context(
            employee_id=employee.id,
            default_employee_id=employee.id,
        ).search(self._leave_type_domain(employee))
        
        allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
        ])

        values = {
            **self._ess_base_values(employee, 'leaves'),
            'leave_types': leave_types,
            'allocations': allocations,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_leave_new', values)

    @http.route('/my/leaves/submit', type='jsonrpc', auth='user')
    def ess_leave_submit(self, leave_id, **kwargs):
        """JSON-RPC endpoint: submit a leave."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}
        leave = request.env['hr.leave'].sudo().search([
            ('id', '=', int(leave_id)),
            ('employee_id', '=', employee.id),
        ], limit=1)
        if not leave.exists():
            return {'success': False, 'error': 'Leave not found.'}
        return leave.action_portal_submit()

    @http.route('/my/leaves/cancel', type='jsonrpc', auth='user')
    def ess_leave_cancel(self, leave_id, **kwargs):
        """JSON-RPC endpoint: cancel a leave."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}
        leave = request.env['hr.leave'].sudo().search([
            ('id', '=', int(leave_id)),
            ('employee_id', '=', employee.id),
        ], limit=1)
        if not leave.exists():
            return {'success': False, 'error': 'Leave not found.'}
        return leave.action_portal_cancel()

    @http.route('/my/leaves/new', type='http', auth='user',
                methods=['POST'])
    def ess_leave_create(self, leave_type_id, date_from, date_to,
                         name='', **kwargs):
        """Create a new leave request from the portal form."""
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()
        try:
            try:
                leave_type_id = int(leave_type_id)
            except (ValueError, TypeError):
                raise UserError('Invalid leave type.')

            # Validate that the leave type is allowed for this employee
            allowed_types = request.env['hr.leave.type'].sudo().search(
                self._leave_type_domain(employee)
            )
            if leave_type_id not in allowed_types.ids:
                raise UserError('This leave type is not available for you.')

            leave = request.env['hr.leave'].sudo().create({
                'employee_id': employee.id,
                'holiday_status_id': leave_type_id,
                'request_date_from': date_from,
                'request_date_to': date_to,
                'name': name,
            })
            leave.action_portal_submit()
        except (ValidationError, UserError) as exc:
            return request.redirect('/my/leaves/new?' + urlencode({'error': str(exc)}))
        return request.redirect('/my/leaves')

    # ------------------------------------------------------------------
    # Attendance – list + check-in/out JSON
    # ------------------------------------------------------------------

    @http.route(['/my/attendance', '/my/attendance/page/<int:page>'], type='http', auth='user')
    def ess_attendance(self, page=1, **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        # Build domain with optional date filters
        domain = [('employee_id', '=', employee.id)]

        date_from = kwargs.get('date_from', '')
        date_to = kwargs.get('date_to', '')

        if date_from:
            try:
                domain.append(('check_in', '>=', f"{date_from} 00:00:00"))
            except:
                pass

        if date_to:
            try:
                domain.append(('check_in', '<=', f"{date_to} 23:59:59"))
            except:
                pass

        Attendance = request.env['hr.attendance'].sudo()
        total = Attendance.search_count(domain)
        pager = portal_pager(
            url='/my/attendance', total=total, page=page, step=_ITEMS_PER_PAGE,
            url_args={'date_from': date_from, 'date_to': date_to, 'grouping': kwargs.get('grouping', 'none')},
        )
        records = Attendance.search(
            domain, order='check_in desc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        # Calculate today and week hours
        today_date = date.today()
        today_start = f"{today_date} 00:00:00"
        today_end = f"{today_date} 23:59:59"

        from datetime import timedelta
        week_start = today_date - timedelta(days=today_date.weekday())
        week_start_str = f"{week_start} 00:00:00"
        week_end_str = f"{today_date} 23:59:59"

        today_att = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
        ])
        today_hours = sum(today_att.mapped('worked_hours'))
        today_records = len(today_att)

        week_att = Attendance.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', week_start_str),
            ('check_in', '<=', week_end_str),
        ])
        week_hours = sum(week_att.mapped('worked_hours'))
        week_records = len(week_att)

        values = {
            **self._ess_base_values(employee, 'attendance'),
            'attendances': records,
            'pager': pager,
            'today_hours': round(float(today_hours), 2),
            'today_records': today_records,
            'week_hours': round(float(week_hours), 2),
            'week_records': week_records,
            'date_from': date_from,
            'date_to': date_to,
            'grouping': kwargs.get('grouping', 'none'),
        }
        return request.render('hr_ess_portal.portal_attendance', values)

    @http.route('/my/attendance/checkin', type='jsonrpc', auth='user')
    def ess_checkin(self, **kwargs):
        """Create an open attendance record (check-in)."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}
        if employee.sudo().ess_is_checked_in:
            return {'success': False, 'error': 'Already checked in.'}
        request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
        })
        return {'success': True}

    @http.route('/my/attendance/checkout', type='jsonrpc', auth='user')
    def ess_checkout(self, **kwargs):
        """Close the open attendance record (check-out)."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}
        open_att = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)
        if not open_att:
            return {'success': False, 'error': 'Not checked in.'}
        from odoo.fields import Datetime
        open_att.sudo().check_out = Datetime.now()
        return {'success': True, 'worked_hours': round(open_att.worked_hours, 2)}

    @http.route('/my/attendance/request-correction', type='http', auth='user')
    def ess_attendance_correction_form(self, **kwargs):
        """Show form to request attendance correction."""
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        # Get employee's pending/approved corrections
        corrections = request.env['hr.attendance.correction'].sudo().search([
            ('employee_id', '=', employee.id),
        ], order='create_date desc', limit=10)

        values = {
            **self._ess_base_values(employee, 'attendance'),
            'corrections': corrections,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_attendance_correction', values)

    @http.route('/my/attendance/request-correction', type='http', auth='user', methods=['POST'])
    def ess_attendance_correction_create(self, attendance_date, correction_type, check_in_time='',
                                          check_out_time='', reason='', **kwargs):
        """Submit an attendance correction request."""
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        try:
            check_in_time = float(check_in_time) if check_in_time else None
            check_out_time = float(check_out_time) if check_out_time else None

            vals = {
                'employee_id': employee.id,
                'attendance_date': attendance_date,
                'correction_type': correction_type,
                'reason': reason,
            }

            if correction_type in ('check_in', 'both'):
                if not check_in_time:
                    raise UserError('Check-in time is required.')
                vals['check_in_time'] = check_in_time

            if correction_type in ('check_out', 'both'):
                if not check_out_time:
                    raise UserError('Check-out time is required.')
                vals['check_out_time'] = check_out_time

            request.env['hr.attendance.correction'].sudo().create(vals)
        except (ValidationError, UserError, ValueError) as exc:
            return request.redirect('/my/attendance/request-correction?' + urlencode({'error': str(exc)}))

        return request.redirect('/my/attendance/request-correction')

    # ------------------------------------------------------------------
    # Payslips – list + PDF download
    # ------------------------------------------------------------------

    @http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', auth='user')
    def ess_payslips(self, page=1, month_filter='', **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        # Get all payslips to build the month filter
        all_payslips = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['done', 'paid', 'validate']),
        ], order='date_from desc')

        # Create a set of unique months (YYYY-MM)
        available_months = sorted(list(set(
            p.date_from.strftime('%Y-%m') for p in all_payslips
        )))

        domain = [
            ('employee_id', '=', employee.id),
            ('state', 'in', ['done', 'paid', 'validate']),
        ]
        if month_filter:
            try:
                month_start, month_end = self._month_bounds(month_filter)
                if not month_start or not month_end:
                    raise ValueError('Invalid month format')
                domain += [
                    ('date_from', '>=', month_start),
                    ('date_from', '<=', month_end),
                ]
            except (ValueError, TypeError):
                return request.redirect('/my/payslips?' + urlencode({'error': 'Invalid month filter format. Use YYYY-MM.'}))

        
        total = len(all_payslips) if not month_filter else request.env['hr.payslip'].sudo().search_count(domain)
        
        pager = portal_pager(
            url='/my/payslips', total=total, page=page, step=_ITEMS_PER_PAGE,
            url_args={'month_filter': month_filter},
        )
        
        payslips = request.env['hr.payslip'].sudo().search(
            domain, order='date_from desc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )
        
        values = {
            **self._ess_base_values(employee, 'payslips'),
            'payslips': payslips,
            'pager': pager,
            'available_months': available_months,
            'month_filter': month_filter,
        }
        return request.render('hr_ess_portal.portal_payslips', values)

    @http.route('/my/payslips/<int:payslip_id>/pdf', type='http',
                auth='user')
    def ess_payslip_pdf(self, payslip_id, **kwargs):
        """Stream the payslip PDF using Odoo's standard report engine."""
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        # Security check: ensure the user can only access their own done/paid payslips
        payslip = request.env['hr.payslip'].sudo().search([
            ('id', '=', payslip_id),
            ('employee_id', '=', employee.id),
            ('state', 'in', ['done', 'paid']),
        ], limit=1)

        if not payslip:
            return request.not_found()

        # Sudo to bypass the access error on hr.employee's lang field
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'hr_payroll.action_report_payslip', payslip.id
        )
        # Sanitize filename to prevent HTTP header injection
        safe_name = (payslip.name or str(payslip_id)).replace('"', '').replace('\n', '').replace('\r', '')
        filename = f"payslip_{safe_name}.pdf"
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
                ('Content-Length', len(pdf_content)),
            ],
        )

    # ------------------------------------------------------------------
    # Expenses – list + create
    # ------------------------------------------------------------------

    @http.route(['/my/expenses', '/my/expenses/page/<int:page>'], type='http', auth='user')
    def ess_expenses(self, page=1, state_filter='all', **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        domain = [('employee_id', '=', employee.id)]
        if state_filter != 'all':
            domain.append(('state', '=', state_filter))

        total = request.env['hr.expense'].sudo().search_count(domain)
        pager = portal_pager(
            url='/my/expenses', total=total, page=page, step=_ITEMS_PER_PAGE,
            url_args={'state_filter': state_filter},
        )
        expenses = request.env['hr.expense'].sudo().search(
            domain, order='date desc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )
        values = {
            **self._ess_base_values(employee, 'expenses'),
            'expenses': expenses,
            'pager': pager,
            'state_filter': state_filter,
        }
        return request.render('hr_ess_portal.portal_expenses', values)

    @http.route('/my/expenses/new', type='http', auth='user', methods=['GET'])
    def ess_expense_new(self, **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()
        categories = request.env['product.product'].sudo().search([
            ('can_be_expensed', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', employee.company_id.id),
        ], order='name')
        values = {
            **self._ess_base_values(employee, 'expenses'),
            'categories': categories,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_expense_new', values)

    # ------------------------------------------------------------------
    # Holiday Calendar
    # ------------------------------------------------------------------

    @http.route('/my/calendar', type='http', auth='user')
    def ess_calendar(self, year=None, month=None, **kwargs):
        """Read-only calendar: public holidays + employee's own approved/pending leaves."""
        from datetime import date as date_cls, timedelta

        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        today = date_cls.today()
        try:
            year = int(year) if year else today.year
            month = int(month) if month else today.month
            if not (1 <= month <= 12):
                raise ValueError
            date_cls(year, month, 1)  # validate year too
        except (ValueError, TypeError):
            year, month = today.year, today.month

        first_day = date_cls(year, month, 1)
        last_day_num = monthrange(year, month)[1]
        last_day = date_cls(year, month, last_day_num)

        prev_date = first_day - timedelta(days=1)
        next_date = last_day + timedelta(days=1)

        # Public holidays: resource.calendar.leaves with no specific resource
        emp_sudo = employee.sudo()
        ph_domain = [
            ('resource_id', '=', False),
            ('date_from', '<=', str(last_day) + ' 23:59:59'),
            ('date_to', '>=', str(first_day) + ' 00:00:00'),
        ]
        if emp_sudo.resource_calendar_id:
            ph_domain += [
                '|',
                ('calendar_id', '=', False),
                ('calendar_id', '=', emp_sudo.resource_calendar_id.id),
            ]
        else:
            ph_domain.append(('calendar_id', '=', False))

        public_holidays = request.env['resource.calendar.leaves'].sudo().search(ph_domain)

        # Employee's own leaves (approved + pending confirmation)
        # Use request_date_from/request_date_to (pure date fields) not date_from/date_to (datetimes)
        leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['validate', 'validate1', 'confirm']),
            ('request_date_from', '<=', last_day),
            ('request_date_to', '>=', first_day),
        ])

        # Build event map: date -> list of event dicts
        events = {}

        for ph in public_holidays:
            # TIMEZONE FIX: Convert UTC datetimes to user's local timezone before extracting dates
            # This prevents UTC→Local timezone shifts from misaligning dates
            from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
            from datetime import datetime as dt_cls

            # Get user's timezone
            tz = request.env.user.tz or 'UTC'

            # Convert date_from to user timezone
            date_from_utc = ph.date_from
            if isinstance(date_from_utc, str):
                date_from_utc = dt_cls.strptime(date_from_utc, DEFAULT_SERVER_DATETIME_FORMAT)

            # Convert to user's timezone-aware datetime
            from pytz import timezone as tz_obj
            utc_tz = tz_obj('UTC')
            user_tz = tz_obj(tz)

            if date_from_utc.tzinfo is None:
                date_from_utc = utc_tz.localize(date_from_utc)
            date_from_local = date_from_utc.astimezone(user_tz)

            # Same for date_to
            date_to_utc = ph.date_to
            if isinstance(date_to_utc, str):
                date_to_utc = dt_cls.strptime(date_to_utc, DEFAULT_SERVER_DATETIME_FORMAT)
            if date_to_utc.tzinfo is None:
                date_to_utc = utc_tz.localize(date_to_utc)
            date_to_local = date_to_utc.astimezone(user_tz)

            # Now extract dates from the LOCAL timezone datetimes
            d_start = date_from_local.date()
            d_end = date_to_local.date()

            # Handle exclusive end-date: if end is at 00:00 and after start, subtract 1 day
            if d_end > d_start and date_to_local.hour == 0 and date_to_local.minute == 0:
                d_end = d_end - timedelta(days=1)

            d_start = max(d_start, first_day)
            d_end = min(d_end, last_day)

            # Only add event if the date range is valid
            if d_start <= d_end:
                curr = d_start
                while curr <= d_end:
                    events.setdefault(curr, []).append({
                        'type': 'holiday',
                        'name': ph.name or 'Public Holiday',
                    })
                    curr += timedelta(days=1)
                _logger.debug(f'Holiday "{ph.name}": UTC {ph.date_from}-{ph.date_to} → Local {d_start}-{d_end} ({tz})')

        for leave in leaves:
            d_start = leave.request_date_from or leave.date_from.date()
            d_end = leave.request_date_to or leave.date_to.date()
            if isinstance(d_start, str):
                d_start = date_cls.fromisoformat(d_start)
            if isinstance(d_end, str):
                d_end = date_cls.fromisoformat(d_end)
            d_start = max(d_start, first_day)
            d_end = min(d_end, last_day)
            ev_type = 'leave' if leave.state in ('validate', 'validate1') else 'pending'
            curr = d_start
            while curr <= d_end:
                events.setdefault(curr, []).append({
                    'type': ev_type,
                    'name': leave.holiday_status_id.name or 'Leave',
                })
                curr += timedelta(days=1)

        # Fetch attendance records for the month
        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', f"{first_day} 00:00:00"),
            ('check_in', '<=', f"{last_day} 23:59:59"),
        ])

        # Build attendance map: date -> list of check-in/out records
        attendance_map = {}
        for att in attendances:
            att_date = att.check_in.date()
            if att_date not in attendance_map:
                attendance_map[att_date] = []
            attendance_map[att_date].append(att)

        # Build calendar grid: list of weeks (Monday-Sunday)
        # monthcalendar returns weeks starting Monday, which is standard
        calendar_weeks = []
        for week in monthcalendar(year, month):
            week_days = []
            for day_num in week:
                if day_num == 0:
                    week_days.append(None)
                else:
                    d = date_cls(year, month, day_num)
                    day_attendances = attendance_map.get(d, [])

                    # Calculate total worked hours for the day
                    total_hours = sum(att.worked_hours for att in day_attendances)

                    # Get first check-in and last check-out times
                    check_in_time = None
                    check_out_time = None
                    if day_attendances:
                        check_in_time = min(att.check_in for att in day_attendances)
                        check_outs = [att.check_out for att in day_attendances if att.check_out]
                        check_out_time = max(check_outs) if check_outs else None

                    week_days.append({
                        'day_num': day_num,
                        'events': events.get(d, []),
                        'is_today': d == today,
                        'is_weekend': d.weekday() >= 5,  # Saturday=5, Sunday=6
                        'total_hours': round(total_hours, 2),
                        'check_in_time': check_in_time,
                        'check_out_time': check_out_time,
                    })
            calendar_weeks.append(week_days)

        # Fetch leave allocations for balance display
        allocations = request.env['hr.leave.allocation'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
        ])

        values = {
            **self._ess_base_values(employee, 'calendar'),
            'year': year,
            'month': month,
            'month_name': first_day.strftime('%B %Y'),
            'calendar_weeks': calendar_weeks,
            'prev_year': prev_date.year,
            'prev_month': prev_date.month,
            'next_year': next_date.year,
            'next_month': next_date.month,
            'allocations': allocations,
        }
        return request.render('hr_ess_portal.portal_calendar', values)

    @http.route('/my/expenses/new', type='http', auth='user',
                methods=['POST'])
    def ess_expense_create(self, product_id, amount, date, description='',
                           payment_mode='own_account', **kwargs):
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()
        try:
            product = request.env['product.product'].sudo().browse(int(product_id))
            if not product.exists() or not product.can_be_expensed:
                raise UserError('Please choose a valid expense category.')
            # Verify product is in employee's company
            if product.company_id and product.company_id.id != employee.company_id.id:
                raise UserError('This product is not available in your company.')

            expense = request.env['hr.expense'].sudo().create({
                'employee_id': employee.id,
                'product_id': product.id,
                'date': date,
                'payment_mode': payment_mode,
                'name': description or product.display_name,
                'description': description or False,
                'quantity': 1,
            })
            expense.write({'total_amount_currency': float(amount)})
            expense.with_user(request.env.user).action_submit()
        except (ValidationError, UserError, ValueError) as exc:
            return request.redirect('/my/expenses/new?' + urlencode({'error': str(exc)}))
        return request.redirect('/my/expenses')

    # ------------------------------------------------------------------
    # Projects & Tasks – browse
    # ------------------------------------------------------------------

    @http.route(['/ess/projects', '/ess/projects/page/<int:page>'], type='http', auth='user')
    def ess_projects(self, page=1, **kwargs):
        """List all active projects available for timesheet entry."""
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        Project = request.env['project.project'].sudo()
        domain = [
            ('active', '=', True),
            ('allow_timesheets', '=', True),
        ]

        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        total = Project.search_count(domain)
        pager = portal_pager(
            url='/ess/projects',
            total=total,
            page=page,
            step=_ITEMS_PER_PAGE,
        )

        projects = Project.search(
            domain, order='name asc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        values = {
            **self._ess_base_values(employee, 'projects'),
            'projects': projects,
            'pager': pager,
        }
        return request.render('hr_ess_portal.portal_projects', values)

    @http.route(['/ess/projects/<int:project_id>', '/ess/projects/<int:project_id>/page/<int:page>'], type='http', auth='user')
    def ess_project_detail(self, project_id, page=1, **kwargs):
        """View project details and its tasks."""
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        project = request.env['project.project'].sudo().browse(project_id)
        if not project.exists() or not project.active or not project.allow_timesheets:
            return request.not_found()

        Task = request.env['project.task'].sudo()
        domain = [
            ('project_id', '=', project_id),
            ('active', '=', True),
        ]

        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        total = Task.search_count(domain)
        pager = portal_pager(
            url=f'/ess/projects/{project_id}',
            total=total,
            page=page,
            step=_ITEMS_PER_PAGE,
        )

        tasks = Task.search(
            domain, order='name asc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        values = {
            **self._ess_base_values(employee, 'projects'),
            'project': project,
            'tasks': tasks,
            'pager': pager,
        }
        return request.render('hr_ess_portal.portal_project_detail', values)

    @http.route(['/ess/tasks', '/ess/tasks/page/<int:page>'], type='http', auth='user')
    def ess_tasks(self, page=1, project_id=None, **kwargs):
        """List all active tasks available for timesheet entry."""
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        Task = request.env['project.task'].sudo()
        domain = [('active', '=', True)]

        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        if project_id:
            try:
                project_id = int(project_id)
                domain.append(('project_id', '=', project_id))
            except (ValueError, TypeError):
                project_id = None

        total = Task.search_count(domain)

        # Build URL args for pagination
        url_args = {}
        if project_id:
            url_args['project_id'] = project_id

        pager = portal_pager(
            url='/ess/tasks',
            total=total,
            page=page,
            step=_ITEMS_PER_PAGE,
            url_args=url_args,
        )

        tasks = Task.search(
            domain, order='project_id, name asc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        projects = request.env['project.project'].sudo().search([
            ('active', '=', True),
            ('allow_timesheets', '=', True),
        ], order='name')

        values = {
            **self._ess_base_values(employee, 'tasks'),
            'tasks': tasks,
            'projects': projects,
            'selected_project': project_id,
            'pager': pager,
        }
        return request.render('hr_ess_portal.portal_tasks', values)

    # ------------------------------------------------------------------
    # Timesheets – list + create
    # ------------------------------------------------------------------

    @http.route('/my/timesheets/weekly', type='http', auth='user')
    def ess_timesheets_weekly(self, year=None, week=None, **kwargs):
        """Weekly timesheet view with calendar layout."""
        from datetime import date as date_cls, timedelta
        from datetime import datetime, datetime as dt_cls
        import math

        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        today = date_cls.today()
        try:
            year = int(year) if year else today.year
            # ISO week number (1-53)
            week = int(week) if week else today.isocalendar()[1]
            if not (1 <= week <= 53):
                raise ValueError
        except (ValueError, TypeError):
            year = today.year
            week = today.isocalendar()[1]

        # Calculate week start (Monday) and end (Sunday)
        jan4 = date_cls(year, 1, 4)
        week_start = jan4 - timedelta(days=jan4.weekday())
        week_start = week_start + timedelta(weeks=week - 1)
        week_end = week_start + timedelta(days=6)

        # Fetch timesheet entries for the week
        timesheets = request.env['account.analytic.line'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '>=', week_start),
            ('date', '<=', week_end),
        ], order='date asc')

        # Get recently used projects (last 4 weeks)
        recent_date = week_start - timedelta(weeks=4)
        recent_timesheets = request.env['account.analytic.line'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '>=', recent_date),
            ('project_id', '!=', False),
        ], order='date desc', limit=50)

        # Extract unique projects (maintaining order)
        seen_projects = set()
        recent_projects = []
        for ts in recent_timesheets:
            if ts.project_id.id not in seen_projects and ts.project_id.allow_timesheets:
                recent_projects.append(ts.project_id)
                seen_projects.add(ts.project_id.id)
                if len(recent_projects) >= 10:
                    break

        # Build day map
        day_data = {}
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_data[current_date] = {
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'entries': [],
                'total_hours': 0,
                'is_today': current_date == today,
                'is_weekend': current_date.weekday() >= 5,
            }

        # Assign entries to days
        for ts in timesheets:
            if ts.date in day_data:
                day_data[ts.date]['entries'].append(ts)
                day_data[ts.date]['total_hours'] += ts.unit_amount

        # Get projects for quick select
        projects = request.env['project.project'].sudo().search([
            ('active', '=', True),
            ('allow_timesheets', '=', True),
        ], order='name')

        # Navigation
        prev_week = week - 1 if week > 1 else 53
        prev_year = year if week > 1 else year - 1
        next_week = week + 1 if week < 53 else 1
        next_year = year if week < 53 else year + 1

        # Weekly total
        weekly_total = sum(d['total_hours'] for d in day_data.values())

        values = {
            **self._ess_base_values(employee, 'timesheets'),
            'year': year,
            'week': week,
            'week_start': week_start,
            'week_end': week_end,
            'day_data': [day_data[week_start + timedelta(days=i)] for i in range(7)],
            'projects': projects,
            'recent_projects': recent_projects,
            'timesheets': timesheets,
            'weekly_total': round(weekly_total, 2),
            'prev_year': prev_year,
            'prev_week': prev_week,
            'next_year': next_year,
            'next_week': next_week,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_timesheets_weekly', values)

    @http.route(['/my/timesheets', '/my/timesheets/page/<int:page>'], type='http', auth='user')
    def ess_timesheets(self, page=1, state_filter='all', **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        domain = [('employee_id', '=', employee.id)]
        if state_filter == 'submitted':
            domain.append(('is_submitted', '=', True))
        elif state_filter == 'pending':
            domain.append(('is_submitted', '=', False))

        TimeSheet = request.env['account.analytic.line'].sudo()
        total = TimeSheet.search_count(domain)
        pager = portal_pager(
            url='/my/timesheets',
            total=total,
            page=page,
            step=_ITEMS_PER_PAGE,
            url_args={'state_filter': state_filter},
        )
        timesheets = TimeSheet.search(
            domain, order='date desc',
            limit=_ITEMS_PER_PAGE, offset=pager['offset'],
        )

        values = {
            **self._ess_base_values(employee, 'timesheets'),
            'timesheets': timesheets,
            'pager': pager,
            'state_filter': state_filter,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_timesheets', values)

    @http.route('/my/timesheets/new', type='http', auth='user', methods=['GET'])
    def ess_timesheet_new(self, **kwargs):
        redirect = self._check_is_portal_user_or_redirect()
        if redirect:
            return redirect
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        projects = request.env['project.project'].sudo().search([
            ('active', '=', True),
            ('allow_timesheets', '=', True),
        ], order='name')

        values = {
            **self._ess_base_values(employee, 'timesheets'),
            'projects': projects,
            'error': kwargs.get('error'),
        }
        return request.render('hr_ess_portal.portal_timesheet_new', values)

    @http.route('/my/timesheets/new', type='http', auth='user', methods=['POST'])
    def ess_timesheet_create(self, project_id, task_id, date, hours, description='', **kwargs):
        employee = self._get_employee_or_404()
        if not employee:
            return request.not_found()

        try:
            project_id = int(project_id) if project_id else None
            task_id = int(task_id) if task_id else None
            hours = float(hours)

            if hours <= 0:
                raise UserError('Hours must be greater than 0.')
            if hours > 24:
                raise UserError('Hours cannot exceed 24 per day.')
            if not project_id:
                raise UserError('Please select a project.')

            timesheet = request.env['account.analytic.line'].sudo().create({
                'employee_id': employee.id,
                'project_id': project_id,
                'task_id': task_id,
                'date': date,
                'unit_amount': hours,
                'name': description or 'Timesheet Entry',
                'is_portal_entry': True,
            })
            _logger.info('Timesheet created: %s', timesheet.id)
        except (ValidationError, UserError, ValueError) as exc:
            return request.redirect('/my/timesheets/new?' + urlencode({'error': str(exc)}))
        return request.redirect('/my/timesheets')

    @http.route('/my/timesheets/submit', type='jsonrpc', auth='user')
    def ess_timesheet_submit(self, timesheet_id, **kwargs):
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}

        timesheet = request.env['account.analytic.line'].sudo().search([
            ('id', '=', int(timesheet_id)),
            ('employee_id', '=', employee.id),
        ], limit=1)
        if not timesheet.exists():
            return {'success': False, 'error': 'Timesheet not found.'}

        return timesheet.action_portal_submit()

    @http.route('/my/timesheets/delete', type='jsonrpc', auth='user')
    def ess_timesheet_delete(self, timesheet_id, **kwargs):
        """Delete a timesheet entry."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}

        try:
            timesheet = request.env['account.analytic.line'].sudo().search([
                ('id', '=', int(timesheet_id)),
                ('employee_id', '=', employee.id),
            ], limit=1)

            if not timesheet.exists():
                return {'success': False, 'error': 'Entry not found.'}

            if timesheet.is_submitted:
                return {'success': False, 'error': 'Cannot delete submitted timesheets.'}

            timesheet.unlink()
            _logger.info('Timesheet deleted: %s', timesheet_id)
            return {'success': True}
        except Exception as exc:
            _logger.warning('Delete failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    @http.route('/my/timesheets/update', type='jsonrpc', auth='user')
    def ess_timesheet_update(self, timesheet_id, hours, task_id=None, description='', **kwargs):
        """Update a timesheet entry."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}

        try:
            timesheet = request.env['account.analytic.line'].sudo().search([
                ('id', '=', int(timesheet_id)),
                ('employee_id', '=', employee.id),
            ], limit=1)

            if not timesheet.exists():
                return {'success': False, 'error': 'Entry not found.'}

            if timesheet.is_submitted:
                return {'success': False, 'error': 'Cannot edit submitted timesheets.'}

            hours = float(hours)
            if hours <= 0 or hours > 24:
                raise UserError('Hours must be between 0.25 and 24.')

            task_id = int(task_id) if task_id else None
            timesheet.write({
                'unit_amount': hours,
                'task_id': task_id,
                'name': description or 'Timesheet Entry',
            })

            _logger.info('Timesheet updated: %s', timesheet_id)
            return {'success': True}
        except (ValidationError, UserError, ValueError) as exc:
            _logger.warning('Update failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    @http.route('/my/timesheets/get-tasks', type='jsonrpc', auth='user')
    def ess_timesheet_get_tasks(self, project_id, **kwargs):
        """Load tasks for a selected project."""
        try:
            project_id = int(project_id) if project_id else None
            if not project_id:
                return {'success': False, 'error': 'No project selected.'}

            project = request.env['project.project'].sudo().browse(project_id)
            if not project.exists():
                return {'success': False, 'error': 'Project not found.'}

            # Get all tasks for the project
            tasks = request.env['project.task'].sudo().search([
                ('project_id', '=', project_id),
                ('active', '=', True),
            ], order='name')

            task_data = [
                {'id': task.id, 'name': task.name}
                for task in tasks
            ]

            return {
                'success': True,
                'tasks': task_data,
                'project_name': project.name,
            }
        except Exception as exc:
            _logger.warning('Get tasks failed: %s', exc)
            return {'success': False, 'error': str(exc)}

    @http.route('/my/timesheets/get-entry', type='jsonrpc', auth='user')
    def ess_timesheet_get_entry(self, date, project_id, task_id=None, **kwargs):
        """Get existing timesheet entry for prefilling modal."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'entry': None}

        try:
            from datetime import datetime
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()

            TimeSheet = request.env['account.analytic.line'].sudo()
            domain = [
                ('employee_id', '=', employee.id),
                ('date', '=', date_obj),
                ('project_id', '=', int(project_id)),
            ]
            if task_id:
                domain.append(('task_id', '=', int(task_id)))
            else:
                domain.append(('task_id', '=', False))

            entry = TimeSheet.search(domain, limit=1)

            if entry:
                return {
                    'entry': {
                        'id': entry.id,
                        'hours': entry.unit_amount,
                        'description': entry.name,
                        'is_submitted': entry.is_submitted,
                    }
                }
            return {'entry': None}
        except Exception as exc:
            _logger.warning('Get entry failed: %s', exc)
            return {'entry': None}

    @http.route('/my/timesheets/quick-entry', type='jsonrpc', auth='user')
    def ess_timesheet_quick_entry(self, date, project_id, hours, task_id=None, description='', entry_id=None, **kwargs):
        """Quick entry for weekly view - create or update."""
        employee = self._get_employee_or_404()
        if not employee:
            return {'success': False, 'error': 'No employee linked.'}

        try:
            project_id = int(project_id) if project_id else None
            task_id = int(task_id) if task_id else None
            hours = float(hours)
            entry_id = int(entry_id) if entry_id else None

            if hours <= 0:
                raise UserError('Hours must be greater than 0.')
            if hours > 24:
                raise UserError('Hours cannot exceed 24 per day.')
            if not project_id:
                raise UserError('Please select a project.')

            # Validate task if provided
            if task_id:
                task = request.env['project.task'].sudo().browse(task_id)
                if not task.exists() or task.project_id.id != project_id:
                    raise UserError('Invalid task for selected project.')

            TimeSheet = request.env['account.analytic.line'].sudo()

            # Update existing entry or create new one
            if entry_id:
                timesheet = TimeSheet.browse(entry_id)
                if not timesheet.exists() or timesheet.employee_id.id != employee.id:
                    raise UserError('Entry not found or access denied.')

                if timesheet.is_submitted:
                    raise UserError('Cannot update a submitted timesheet. Please unsubmit first.')

                timesheet.write({
                    'unit_amount': hours,
                    'name': description or 'Timesheet Entry',
                })
                _logger.info('Quick timesheet entry updated: %s', timesheet.id)
            else:
                timesheet = TimeSheet.create({
                    'employee_id': employee.id,
                    'project_id': project_id,
                    'task_id': task_id,
                    'date': date,
                    'unit_amount': hours,
                    'name': description or 'Timesheet Entry',
                    'is_portal_entry': True,
                })
                _logger.info('Quick timesheet entry created: %s', timesheet.id)

            return {'success': True, 'timesheet_id': timesheet.id}
        except (ValidationError, UserError, ValueError) as exc:
            _logger.warning('Quick entry failed: %s', exc)
            return {'success': False, 'error': str(exc)}
