import frappe

from dashboard.services.common import master_count


def get_widgets(filters):
    return {
        "active_employees": master_count("Employee", {"status": "Active"}),
        "attendance_pct": get_attendance_pct(filters),
        "pending_leave_requests": frappe.db.count(
            "Leave Application", filters={"status": "Open", "company": ["in", filters.companies]}
        ),
        "upcoming_payroll": get_upcoming_payroll(filters),
    }


def get_attendance_pct(filters):
    rows = frappe.db.sql(
        """
        select sum(case when status = 'Present' then 1 else 0 end) as present,
               count(*) as total
        from `tabAttendance`
        where company in %(companies)s
          and attendance_date between %(from_date)s and %(to_date)s
          and docstatus = 1
        """,
        {"companies": filters.companies, "from_date": filters.from_date, "to_date": filters.to_date},
        as_dict=True,
    )
    if not rows or not rows[0].total:
        return 0
    return round((rows[0].present or 0) / rows[0].total * 100, 1)


def get_upcoming_payroll(filters):
    rows = frappe.get_all(
        "Payroll Entry",
        filters={"company": ["in", filters.companies], "status": "Draft"},
        fields=["name", "start_date", "end_date"],
        order_by="start_date asc",
        limit_page_length=1,
    )
    return rows[0] if rows else None
