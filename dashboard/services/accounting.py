import frappe
from frappe.utils import flt

from dashboard.queries import ageing, financial, rankings, trends
from dashboard.services.common import doc_status_card


def get_widgets(filters):
    payables = ageing.get_payables_ageing(filters)
    receivables = ageing.get_receivables_ageing(filters)
    income = financial.get_income_summary(filters)
    expense = financial.get_expense_summary(filters)
    return {
        "payment_request": doc_status_card("Payment Request", filters, date_field="transaction_date"),
        "journal_entry": doc_status_card("Journal Entry", filters, date_field="posting_date"),
        "payment_entry": doc_status_card("Payment Entry", filters, date_field="posting_date"),
        "payables": {"total": payables["total"], "overdue": payables["overdue"]},
        "receivables": {"total": receivables["total"], "overdue": receivables["overdue"]},
        "payables_ageing": payables["buckets"],
        "receivables_ageing": receivables["buckets"],
        "income": income,
        "expense": expense,
        "net_surplus": financial.get_net_surplus(filters, income["total"], expense["total"]),
        "expenses_by_category": financial.get_expenses_by_category(filters),
        "monthly_trend": trends.get_monthly_trend(filters),
        "top_suppliers": rankings.get_top_suppliers(filters),
        "top_customers": rankings.get_top_customers(filters),
        "cash_position": get_cash_position(filters),
    }


def get_cash_position(filters):
    accounts = frappe.get_all(
        "Account",
        filters={"company": ["in", filters.companies], "account_type": ["in", ["Bank", "Cash"]], "is_group": 0},
        fields=["name", "account_name", "account_type"],
    )
    balances = []
    total = 0.0
    for acc in accounts:
        balance = flt(
            frappe.db.sql(
                """
                select sum(debit - credit)
                from `tabGL Entry`
                where account = %(account)s
                  and posting_date <= %(as_of)s
                  and is_cancelled = 0
                """,
                {"account": acc.name, "as_of": filters.to_date},
            )[0][0]
            or 0
        )
        if balance:
            balances.append({"account": acc.account_name, "type": acc.account_type, "balance": balance})
            total += balance
    return {"total": total, "accounts": balances}


def get_document_status_summary(filters, all_widgets):
    totals = {}
    for module_widgets in all_widgets.values():
        if not isinstance(module_widgets, dict):
            continue
        for widget in module_widgets.values():
            if isinstance(widget, dict) and "by_status" in widget:
                for entry in widget["by_status"]:
                    totals[entry["status"]] = totals.get(entry["status"], 0) + entry["count"]
    grand_total = sum(totals.values())
    if not grand_total:
        return {"total": 0, "by_status": []}
    return {
        "total": grand_total,
        "by_status": [
            {"status": status, "count": count, "pct": round(count / grand_total * 100, 1)}
            for status, count in sorted(totals.items(), key=lambda item: -item[1])
        ],
    }
