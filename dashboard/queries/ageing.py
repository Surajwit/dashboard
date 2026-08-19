import frappe
from frappe.utils import flt

BUCKETS = [
    ("0-30 Days", 0, 30),
    ("31-60 Days", 31, 60),
    ("61-90 Days", 61, 90),
    ("91-180 Days", 91, 180),
    ("180+ Days", 181, None),
]


def _ageing(doctype, party_field, filters):
    if not filters.companies:
        return {"total": 0, "overdue": 0, "buckets": [{"label": label, "amount": 0, "pct": 0} for label, _, _ in BUCKETS]}
    meta = frappe.get_meta(doctype)
    conditions = {"company": ["in", filters.companies], "docstatus": 1, "outstanding_amount": [">", 0]}
    if filters.branch and meta.has_field("branch"):
        conditions["branch"] = filters.branch
    if filters.cost_center and meta.has_field("cost_center"):
        conditions["cost_center"] = filters.cost_center
    fields = ["name", "outstanding_amount", "due_date", "posting_date", party_field]
    invoices = frappe.get_all(doctype, filters=conditions, fields=fields, limit_page_length=0)

    buckets = {label: 0.0 for label, _, _ in BUCKETS}
    total = 0.0
    overdue_total = 0.0
    for inv in invoices:
        due = inv.due_date or inv.posting_date
        days_overdue = max((filters.to_date - due).days, 0)
        amount = flt(inv.outstanding_amount)
        total += amount
        if days_overdue > 0:
            overdue_total += amount
        for label, lo, hi in BUCKETS:
            if days_overdue >= lo and (hi is None or days_overdue <= hi):
                buckets[label] += amount
                break

    return {
        "total": total,
        "overdue": overdue_total,
        "buckets": [
            {"label": label, "amount": buckets[label], "pct": round(buckets[label] / total * 100, 1) if total else 0}
            for label, _, _ in BUCKETS
        ],
    }


def get_payables_ageing(filters):
    return _ageing("Purchase Invoice", "supplier", filters)


def get_receivables_ageing(filters):
    return _ageing("Sales Invoice", "customer", filters)
