# Screenshots Guide

## Location

Screenshots are stored in a **separate folder** and referenced from `index.html`:

```
hr_ess_portal/
├── screenshots/                    (Your screenshots folder)
│   ├── 01-dashboard.png           ✅ (Already added)
│   ├── 02-leave-request.png       ✅
│   ├── 03-attendance-clock.png    ✅
│   ├── 04-attendance-correction.png
│   ├── 05-timesheet-weekly.png    ✅
│   ├── 06-timesheet-modal.png
│   ├── 07-payslips.png            ✅
│   ├── 08-expense-form.png        ✅
│   ├── 09-projects.png            ✅
│   ├── 10-tasks.png
│   └── 11-calender-view.png       ✅
│
└── static/description/
    ├── index.html                 ✅ (References screenshots folder)
    └── icon.png                   (optional - app icon, 256x256)
```

## Path Reference in index.html

The `index.html` uses relative paths to reference screenshots:
- `../../../screenshots/01-dashboard.png`

This translates to:
```
static/description/index.html
└── ../../../ (go up 3 levels)
    └── screenshots/ (your screenshots folder)
```

## Screenshot Requirements

### Format
- **File Format**: PNG (recommended) or JPG
- **Resolution**: 1024x768 minimum (landscape) or 768x1024 (portrait)
- **Aspect Ratio**: 4:3 or 16:9 recommended
- **File Size**: < 500KB per image

### Current File Names (Already in your folder)
The `index.html` references these files from the `screenshots/` folder:
1. `01-dashboard.png` — Dashboard overview ✅
2. `02-leave-request.png` — Leave request form ✅
3. `03-attendance-clock.png` — Attendance clock ✅
4. `04-attendance-correction.png` — Attendance corrections
5. `05-timesheet-weekly.png` — Weekly timesheet ✅
6. `06-timesheet-modal.png` — Timesheet modal
7. `07-payslips.png` — Payslips view ✅
8. `08-expense-form.png` — Expense claims ✅
9. `09-projects.png` — Projects list ✅
10. `10-tasks.png` — Tasks view
11. `11-calender-view.png` — Leave calendar ✅

## What to Screenshot

### 1. Dashboard (`screenshot_01_dashboard.png`)
- Show the main dashboard with:
  - Leave request status widget
  - Attendance status
  - Quick-action buttons
  - Pending approvals count

### 2. Leave Request (`screenshot_02_leave_request.png`)
- Leave request form showing:
  - Date range picker
  - Leave type selection
  - Request submission

### 3. Attendance (`screenshot_03_attendance.png`)
- Attendance page with:
  - Clock in/out buttons
  - Current status indicator
  - Recent clock records

### 4. Timesheet (`screenshot_04_timesheet.png`)
- Weekly timesheet view showing:
  - Weekly calendar grid
  - Project/task entries
  - Day totals
  - Submit button

### 5. Payslips (`screenshot_05_payslips.png`)
- Payslip list showing:
  - Payslip records
  - Dates
  - Download buttons
  - Salary summary

### 6. Expenses (`screenshot_06_expenses.png`)
- Expense management showing:
  - Expense form
  - Amount and category
  - Receipt attachment
  - Status tracking

### 7. Projects (`screenshot_07_projects.png`)
- Projects page showing:
  - Active projects list
  - Project details
  - Quick project access

### 8. Mobile (`screenshot_08_mobile.png`)
- Mobile responsive view showing:
  - Dashboard on mobile
  - Responsive layout
  - Touch-friendly buttons
  - Menu on mobile device

## Optional: App Icon

Create a 256x256 PNG image with your app branding and save as:
- `icon.png` — App icon for store listing

## Odoo App Store Display

When you submit to the Odoo App Store (apps.odoo.com):
- The `index.html` will be displayed on your app's listing page
- Screenshots will appear in a gallery
- The `icon.png` will be used as the app icon
- Users will see all content from your HTML file

## Pro Tips

1. **Use High Resolution**: Capture screenshots at high resolution for clarity
2. **Add Captions**: Each screenshot already has a caption in the HTML
3. **Show Real Data**: Include realistic employee data in screenshots
4. **Highlight Features**: Make sure key features are visible in each screenshot
5. **Consistent Branding**: Use the Neo-Brutalist color scheme (#6b4c7a purple)
6. **Mobile Version**: Show both desktop and mobile views

## Testing

After adding screenshots:
1. Open `index.html` in a browser
2. Verify all images load properly
3. Check responsive design (desktop and mobile)
4. Ensure file paths are correct

---

**Next Steps:**
1. Capture screenshots of your running module
2. Save them with the names listed above
3. Place them in `static/description/` folder
4. Test the HTML file in a browser
5. Submit to Odoo App Store!