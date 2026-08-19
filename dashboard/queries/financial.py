from dateutil.relativedelta import relativedelta

import frappe
from frappe.utils import flt


def _sum_by_root_type(root_type, filters, other_account_types=None):
    if not filters.companies:
        return 0, 0, 0
    conditions, params = filters.gl_conditions()
    other_account_types = other_account_types or []
    rows = frappe.db.sql(
        f"""
        select acc.account_type, sum(gl.credit - gl.debit) as balance
        from `tabGL Entry` gl
        inner join `tabAccount` acc on acc.name = gl.account
        where acc.root_type = %(root_type)s and {conditions}
        group by acc.account_type
        """,
        {**params, "root_type": root_type},
        as_dict=True,
    )
    total = sum(flt(row.balance) for row in rows)
    other = sum(flt(row.balance) for row in rows if row.account_type in other_account_types)
    operating = total - other
    if root_type == "Expense":
        total, other, operating = -total, -other, -operating
    return total, operating, other


def get_income_summary(filters):
    total, operating, other = _sum_by_root_type("Income", filters, ["Other Income"])
    return {"total": total, "operating": operating, "other": other, "yoy_pct": _yoy_change(filters, "Income", total)}


def get_expense_summary(filters):
    total, operating, other = _sum_by_root_type("Expense", filters, ["Depreciation", "Other Expense"])
    return {"total": total, "operating": operating, "other": other, "yoy_pct": _yoy_change(filters, "Expense", total)}


def get_net_surplus(filters, income_total=None, expense_total=None):
    income_total = get_income_summary(filters)["total"] if income_total is None else income_total
    expense_total = get_expense_summary(filters)["total"] if expense_total is None else expense_total
    net = income_total - expense_total
    prior_net = _prior_year_total(filters, "Income") - _prior_year_total(filters, "Expense")
    return {"total": net, "yoy_pct": _pct_change(prior_net, net)}


def get_expenses_by_category(filters):
    if not filters.companies:
        return []
    conditions, params = filters.gl_conditions()
    rows = frappe.db.sql(
        f"""
        select coalesce(acc.parent_account, acc.account) as category,
               sum(gl.debit - gl.credit) as amount
        from `tabGL Entry` gl
        inner join `tabAccount` acc on acc.name = gl.account
        where acc.root_type = 'Expense' and {conditions}
        group by category
        order by amount desc
        """,
        params,
        as_dict=True,
    )
    total = sum(flt(row.amount) for row in rows) or 1
    for row in rows:
        row["pct"] = round(flt(row.amount) / total * 100, 1)
    return rows[:8]


def _prior_year_total(filters, root_type):
    from dashboard.utils.filters import DashboardFilters
    prior = DashboardFilters(
        from_date=filters.from_date - relativedelta(years=1),
        to_date=filters.to_date - relativedelta(years=1),
        companies=filters.companies,
        branch=filters.branch,
        cost_center=filters.cost_center,
    )
    total, _, _ = _sum_by_root_type(root_type, prior)
    return total


def _yoy_change(filters, root_type, current_total):
    return _pct_change(_prior_year_total(filters, root_type), current_total)


def _pct_change(prior, current):
    if not prior:
        return 0.0
    return round((flt(current) - flt(prior)) / abs(flt(prior)) * 100, 2)
