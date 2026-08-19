import frappe
from frappe.utils import flt


def _top_parties(doctype, party_field, filters, limit=5):
    meta = frappe.get_meta(doctype)
    conditions = {"company": ["in", filters.companies], "docstatus": 1, "outstanding_amount": [">", 0]}
    if filters.branch and meta.has_field("branch"):
        conditions["branch"] = filters.branch
    if filters.cost_center and meta.has_field("cost_center"):
        conditions["cost_center"] = filters.cost_center
    rows = frappe.get_all(doctype, filters=conditions, fields=[party_field, "outstanding_amount", "due_date", "posting_date"], limit_page_length=0)
    totals, overdue = {}, {}
    for row in rows:
        party = row.get(party_field) or "Unknown"
        amount = flt(row.outstanding_amount)
        totals[party] = totals.get(party, 0) + amount
        due = row.due_date or row.posting_date
        if due and (filters.to_date - due).days > 0:
            overdue[party] = overdue.get(party, 0) + amount
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"party": party, "amount": amount, "overdue": overdue.get(party, 0)} for party, amount in ranked]


def get_top_suppliers(filters, limit=5):
    return _top_parties("Purchase Invoice", "supplier", filters, limit)


def get_top_customers(filters, limit=5):
    return _top_parties("Sales Invoice", "customer", filters, limit)
