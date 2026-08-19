import frappe
from frappe.utils import flt, formatdate


def get_monthly_trend(filters):
    if not filters.companies:
        return []
    conditions, params = filters.gl_conditions()
    rows = frappe.db.sql(
        f"""
        select date_format(gl.posting_date, '%%Y-%%m') as month,
               acc.root_type,
               sum(gl.credit - gl.debit) as net_credit
        from `tabGL Entry` gl
        inner join `tabAccount` acc on acc.name = gl.account
        where acc.root_type in ('Income', 'Expense') and {conditions}
        group by month, acc.root_type
        order by month
        """,
        params,
        as_dict=True,
    )
    by_month = {}
    for row in rows:
        item = by_month.setdefault(row.month, {"income": 0.0, "expense": 0.0})
        if row.root_type == "Income":
            item["income"] += flt(row.net_credit)
        else:
            item["expense"] += -flt(row.net_credit)
    return [
        {"month": formatdate(month + "-01", "MMM"), "income": values["income"], "expense": values["expense"], "net_surplus": values["income"] - values["expense"]}
        for month, values in sorted(by_month.items())
    ]
