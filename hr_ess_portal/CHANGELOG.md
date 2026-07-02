# Changelog

All notable changes to the Employee Self-Service Portal (ESS) module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [19.0.1.0.0] - 2024-07-02

### Added

#### Dashboard
- Quick-action button grid with 8 essential functions
- Leave request status breakdown (Pending/Approved/Rejected)
- Attendance status indicator (On Track/Behind/Overtime)
- Upcoming leaves preview section
- Projects overview card
- Quick task count display
- Dynamic task loading with prefilled modal

#### Leave Management
- Leave request creation with type selection
- Refusal workflow with optional reason notes
- Leave balance display with progress bars
- Two-tier approval workflow (confirm → validate states)
- Leave history with filtering

#### Attendance & Corrections
- Clock in/out functionality with visual status
- Today's worked hours tracking
- Weekly hours summary
- Attendance correction request workflow
- Visual attendance status on dashboard

#### Payslips
- Payslip list with pagination
- PDF download functionality
- Latest payslip quick access from dashboard

#### Expenses
- Expense claim submission
- Reimbursement status tracking
- Pending expenses count on dashboard
- Expense sheet management

#### Timesheets
- Weekly calendar view with 7-day grid
- Project/task-based time logging
- Quick-add buttons for recent projects
- Modal prefilling for editing existing entries
- Update/delete unsubmitted entries only
- Entry status indicators (submitted/unsubmitted)
- Weekly total hours calculation
- Color-coded hour totals (green/orange/blue by status)
- Dynamic task population by project
- Search functionality for projects

#### Projects & Tasks
- Project browsing with active/inactive filtering
- Task assignment display
- Task priority indicators
- Task progress bars
- Project-based task filtering
- `/ess/` namespace to avoid base portal conflicts

#### Portal Security
- Row-level security rules for all models
- Portal group-based access control
- User sees only their own records
- Strict domain filtering on all queries

### Technical Implementation

#### Backend
- Python 3.8+ compatible code
- SAVEPOINT-based transaction handling
- JSON-RPC endpoints for AJAX operations
- Proper error handling and logging
- Date/time handling with timezone awareness

#### Frontend
- OWL 3 component integration
- Vanilla JavaScript with window object attachment
- CDATA sections for proper XML escaping
- Modal dialogs for data entry
- Responsive grid layouts
- Neo-Brutalist CSS styling

#### Database
- Custom `is_submitted` field on timesheets
- Security rules via `ir.rule` model
- Efficient pagination with offset/limit
- Portal-friendly security domain rules

### Features
- Portal pager with `/page/<int:page>` URL patterns
- AJAX modal for quick entry with prefilling
- Dynamic form updates based on selections
- Color-coded status indicators
- Responsive mobile-first design

### Security & Performance
- Portal-based RBAC
- Row-level access control
- Efficient database queries with proper indexing
- Transaction safety with SAVEPOINTs
- XSS protection with proper HTML escaping
- CSRF token handling for all AJAX calls

## Future Roadmap

### Planned for v19.0.2.0.0
- [ ] Timesheet approval workflow
- [ ] Leave approval dashboard for managers
- [ ] Email notifications for pending approvals
- [ ] Mobile app optimization
- [ ] Export to CSV functionality

### Planned for v19.1.0.0
- [ ] Multi-language support
- [ ] Custom leave workflows
- [ ] Expense report generation
- [ ] Advanced timesheet analytics
- [ ] Integration with calendar sync

## Known Issues

- None currently known. Please report issues on [GitHub Issues](https://github.com/meet1432/hr-ess-portal/issues)

## Migration Notes

### v19.0.1.0.0
- First stable release
- No database migrations needed
- Backward compatible with Odoo 19 standard modules

## Contributors

- DRC Systems - Initial development
- Community contributors welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

For bug reports, feature requests, and discussions, please visit:
- [GitHub Issues](https://github.com/meet1432/hr-ess-portal/issues)
- [GitHub Discussions](https://github.com/meet1432/hr-ess-portal/discussions)

---

**Last Updated**: July 2024