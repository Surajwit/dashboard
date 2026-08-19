import frappe


def doc_status_card(doctype, filters, date_field="transaction_date", extra_filters=None):
    meta = frappe.get_meta(doctype)
    base_filters = filters.doc_filters(doctype, date_field=date_field)
    if extra_filters:
        base_filters.update({k: v for k, v in extra_filters.items() if meta.has_field(k)})

    fields = ["name"]
    has_status = meta.has_field("status")
    has_docstatus = meta.has_field("docstatus")
    if has_status:
        fields.append("status")
    if has_docstatus:
        fields.append("docstatus")

    rows = frappe.get_all(doctype, filters=base_filters, fields=fields, limit_page_length=0)
    by_status = {}
    for row in rows:
        if has_status:
            status = row.get("status") or ("Submitted" if row.get("docstatus") == 1 else "Draft")
        elif has_docstatus:
            status = "Submitted" if row.get("docstatus") == 1 else "Draft"
        else:
            status = "Active"
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "doctype": doctype,
        "total": len(rows),
        "by_status": [
            {"status": status, "count": count}
            for status, count in sorted(by_status.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def master_count(doctype, extra_filters=None):
    return frappe.db.count(doctype, filters=extra_filters or {})
