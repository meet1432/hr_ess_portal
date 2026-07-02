# -*- coding: utf-8 -*-
{
    'name': 'Employee Self-Service Portal (ESS)',
    'version': '19.0.1.0.0',
    'summary': 'Modern Neo-Brutalist Employee Self-Service Portal for Odoo 19',
    'description': """
        <h3>Modern Employee Self-Service Portal for Odoo 19</h3>
        <p>A comprehensive, beautifully designed portal that empowers employees to self-manage HR processes with ease and security.</p>

        <h4>Core Features</h4>
        <ul>
        <li><strong>Leave Management</strong> - Request, track, and manage leave with approval workflows</li>
        <li><strong>Attendance Tracking</strong> - Clock in/out and request corrections</li>
        <li><strong>Payslips</strong> - View and download payslips securely</li>
        <li><strong>Expense Management</strong> - Submit and track reimbursement claims</li>
        <li><strong>Timesheets</strong> - Log hours by project with weekly calendar view</li>
        <li><strong>Projects & Tasks</strong> - Browse and track assigned work</li>
        <li><strong>Dashboard</strong> - Quick overview of pending approvals and key metrics</li>
        </ul>

        <h4>Why Choose ESS Portal?</h4>
        <ul>
        <li><strong>Clean Design</strong> - Neo-Brutalist aesthetic with intuitive navigation</li>
        <li><strong>Mobile Ready</strong> - Fully responsive on all devices</li>
        <li><strong>Secure by Default</strong> - Row-level access control, users see only their data</li>
        <li><strong>Developer Friendly</strong> - Built on Odoo 19 portal framework with clean code</li>
        <li><strong>Easy to Customize</strong> - Well-documented, modular architecture</li>
        </ul>

        <h4>Perfect For</h4>
        <p>Organizations looking for a modern, user-friendly employee portal that reduces HR burden and improves employee experience.</p>

        <p><strong>Requires:</strong> Odoo 19 Enterprise Edition</p>
        <p><strong>Repository:</strong> Fully open-source on GitHub with contribution guidelines</p>
    """,
    'author': 'meet1432',
    'website': 'https://github.com/meet1432/hr-ess-portal',
    'category': 'Human Resources',
    'license': 'LGPL-3',
    'images': [
        'static/description/cover.png',
    ],
    'depends': [
        'base',
        'portal',
        'mail',
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_expense',
        'hr_payroll',
        'account',
        'project',
        'hr_timesheet',
    ],
    'data': [
        # Security first – always load ir.model.access before views
        'security/ir.model.access.csv',
        'security/hr_ess_portal_rules.xml',
        # Data
        'data/portal_menu_data.xml',
        # Views / Templates
        'views/portal_dashboard_templates.xml',
        'views/portal_calendar_templates.xml',
        'views/portal_leave_templates.xml',
        'views/portal_attendance_templates.xml',
        'views/portal_attendance_correction_templates.xml',
        'views/portal_payslip_templates.xml',
        'views/portal_expense_templates.xml',
        'views/portal_timesheets_templates.xml',
        'views/portal_timesheets_weekly_templates.xml',
        'views/portal_projects_templates.xml',
        'views/portal_tasks_templates.xml',
        # Wizards
        'wizard/leave_request_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hr_ess_portal/static/src/css/ess_portal.css',
            'hr_ess_portal/static/src/js/ess_dashboard.js',
            'hr_ess_portal/static/src/js/leave_wizard.js',
            'hr_ess_portal/static/src/js/attendance_clock.js',
            'hr_ess_portal/static/src/js/timesheet_weekly.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
