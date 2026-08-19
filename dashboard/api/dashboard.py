import json

import frappe

from dashboard.services import accounting, assets, crm, hr, manufacturing, purchase, sales, stock
from dashboard.utils import cache
from dashboard.utils.defaults import DEFAULT_LAYOUT, WIDGET_CATALOG
from dashboard.utils.filters import DashboardFilters

MODULES = {
    "purchase": purchase,
    "sales": sales,
    "accounting": accounting,
    "stock": stock,
    "manufacturing": manufacturing,
    "hr": hr,
    "assets": assets,
    "crm": crm,
}


def _compute(filters):
    widgets = {}
    errors = {}
    for name, module in MODULES.items():
        try:
            widgets[name] = module.get_widgets(filters)
        except Exception:
            errors[name] = frappe.get_traceback()
            frappe.log_error(title=f"dashboard: {name} widget failed", message=frappe.get_traceback())
            widgets[name] = {}

    try:
        document_status_summary = accounting.get_document_status_summary(filters, widgets)
    except Exception:
        document_status_summary = {"total": 0, "by_status": []}
        errors["document_status_summary"] = frappe.get_traceback()

    try:
        recent_activities = get_recent_activities(filters)
    except Exception:
        recent_activities = []
        errors["recent_activities"] = frappe.get_traceback()

    return {
        **widgets,
        "document_status_summary": document_status_summary,
        "recent_activities": recent_activities,
        "filters": filters.as_dict(),
        "errors": {key: True for key in errors},
    }


@frappe.whitelist()
def get_dashboard_data(financial_year=None, from_date=None, to_date=None, companies=None, branch=None, cost_center=None):
    if isinstance(companies, str):
        try:
            companies = json.loads(companies)
        except Exception:
            companies = [companies]
    filters = DashboardFilters(
        financial_year=financial_year,
        from_date=from_date,
        to_date=to_date,
        companies=companies,
        branch=branch,
        cost_center=cost_center,
    )
    return cache.get_or_set("overview_dashboard", filters.as_dict(), lambda: _compute(filters))


@frappe.whitelist()
def get_filter_options():
    result = {
        "companies": frappe.get_list("Company", pluck="name"),
        "fiscal_years": frappe.get_all("Fiscal Year", fields=["name", "year_start_date", "year_end_date"], order_by="year_start_date desc"),
        "branches": [],
        "cost_centers": [],
    }
    if frappe.db.exists("DocType", "Branch"):
        result["branches"] = frappe.get_list("Branch", pluck="name")
    if frappe.db.exists("DocType", "Cost Center"):
        result["cost_centers"] = frappe.get_list("Cost Center", filters={"is_group": 0}, pluck="name")
    return result


@frappe.whitelist()
def get_recent_activities(filters=None, limit=10):
    if isinstance(filters, str):
        filters = DashboardFilters(**json.loads(filters))
    elif not isinstance(filters, DashboardFilters):
        filters = DashboardFilters()

    doctypes = [
        "Purchase Order", "Purchase Invoice", "Sales Order", "Sales Invoice",
        "Payment Request", "Payment Entry", "Journal Entry", "Stock Entry", "Work Order",
    ]
    activities = []
    for dt in doctypes:
        try:
            meta = frappe.get_meta(dt)
            fields = ["name", "modified"]
            has_status = meta.has_field("status")
            if has_status:
                fields.append("status")
            if meta.has_field("docstatus"):
                fields.append("docstatus")
            conditions = {"docstatus": 1} if meta.has_field("docstatus") else {}
            if meta.has_field("company"):
                conditions["company"] = ["in", filters.companies]
            rows = frappe.get_all(dt, filters=conditions, fields=fields, order_by="modified desc", limit_page_length=5)
            for row in rows:
                status = row.get("status") if has_status else None
                if not status:
                    status = "Submitted" if row.get("docstatus") == 1 else "Draft"
                activities.append({"doctype": dt, "name": row.name, "status": status, "timestamp": row.modified})
        except Exception:
            continue
    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[: int(limit)]


@frappe.whitelist()
def get_widget_catalog():
    return WIDGET_CATALOG


@frappe.whitelist()
def get_dashboard_layout():
    user = frappe.session.user
    name = frappe.db.exists("Dashboard Configuration", {"for_user": user, "enabled": 1})
    if not name:
        return DEFAULT_LAYOUT
    doc = frappe.get_doc("Dashboard Configuration", name)
    try:
        layout = json.loads(doc.layout_json or "[]")
        return _sanitize_layout(layout) or DEFAULT_LAYOUT
    except Exception:
        return DEFAULT_LAYOUT


@frappe.whitelist()
def save_dashboard_layout(layout):
    if isinstance(layout, str):
        layout = json.loads(layout)
    layout = _sanitize_layout(layout)
    if not layout:
        frappe.throw("Dashboard layout cannot be empty")

    user = frappe.session.user
    name = frappe.db.exists("Dashboard Configuration", {"for_user": user})
    if name:
        doc = frappe.get_doc("Dashboard Configuration", name)
        doc.layout_json = json.dumps(layout)
        doc.enabled = 1
        doc.version = (doc.version or 0) + 1
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({
            "doctype": "Dashboard Configuration",
            "for_user": user,
            "layout_json": json.dumps(layout),
            "enabled": 1,
            "version": 1,
        })
        doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return layout


@frappe.whitelist()
def reset_dashboard_layout():
    user = frappe.session.user
    name = frappe.db.exists("Dashboard Configuration", {"for_user": user})
    if name:
        frappe.delete_doc("Dashboard Configuration", name, ignore_permissions=True)
        frappe.db.commit()
    return DEFAULT_LAYOUT


def _sanitize_layout(layout):
    if not isinstance(layout, list):
        return []
    allowed = {item["id"]: item for item in WIDGET_CATALOG}
    seen = set()
    result = []
    for item in layout[:100]:
        if not isinstance(item, dict):
            continue
        widget_id = item.get("id")
        if widget_id not in allowed or widget_id in seen:
            continue
        seen.add(widget_id)
        base = allowed[widget_id]
        col = int(item.get("col", base.get("col", 3))) if str(item.get("col", "")).isdigit() else base.get("col", 3)
        if col not in (2, 3, 4, 6, 8, 12):
            col = base.get("col", 3)
        result.append({"id": widget_id, "type": base["type"], "title": str(item.get("title") or base["title"])[:100], "col": col})
    return result
