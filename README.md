# Dashboard

A configurable ERPNext/Frappe dashboard for the ERPNext-style Overview Dashboard design.

## Design language

The UI follows the supplied reference design:

- Navy shell: `#001E42` / `#001F43`
- Primary blue: `#1E73EF`
- Deep text: `#0B1F3A`
- Muted text: `#5F79A1`
- Canvas: `#EEF4F9`
- Cards: `#FFFFFF`
- Borders: `#D0DBE0`
- Purchase purple: `#734CD3`
- Sales green: `#43AE45`
- Payment orange: `#FC970E`
- Receivables teal: `#1CA8AB`
- Danger/overdue red: `#E43938`

The reference image used a very light blue-gray canvas, white cards, dark navy navigation, strong blue action controls, and distinct semantic widget colors. The palette above is intentionally centralized in CSS variables so branding can be changed without rewriting widget code.

## Features

- ERPNext data from standard DocTypes and GL Entry.
- Fiscal year, date, company, branch and cost-center filters.
- Transaction cards, financial summaries, ageing, trends, rankings, document status, recent activity, cash position and shortcuts.
- One failed module/widget does not blank the dashboard; errors are isolated per widget.
- User-configurable dashboard layout: drag widgets, change widget width, add/remove widgets, save and reset.
- Per-user configuration stored in `Dashboard Configuration`.
- Default layout mirrors the supplied Dashboard reference design.
- No changes to ERPNext core.

## Install

```bash
bench get-app https://github.com/Surajwit/dashboard.git
bench --site <site> install-app dashboard
bench --site <site> migrate
bench build --app dashboard
bench restart
```

Open:

```text
/app/dashboard
```

## Configuration model

The dashboard deliberately follows the same configuration idea used by Frappe/ERPNext workspaces: a layout is a list of typed blocks with a width/column value. The implementation keeps the custom visual shell while persisting each user's layout separately.

This means the user can customize the dashboard without changing Python or JavaScript files.

## Important data definitions

- Income: GL Entry credits less debits for `Account.root_type = Income`.
- Expenses: GL Entry debits less credits for `Account.root_type = Expense`.
- Payables: submitted Purchase Invoice outstanding amounts.
- Receivables: submitted Sales Invoice outstanding amounts.
- Ageing: outstanding amounts bucketed by due date as of the selected end date.
- Cash: Bank and Cash account balances from GL Entry.
- Document status: aggregated from transaction cards.

Finance teams should validate these definitions against their organization's accounting policy before using the dashboard for statutory reporting.
