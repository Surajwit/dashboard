import frappe
from frappe.utils import flt

from dashboard.services.common import doc_status_card


def get_widgets(filters):
    return {
        "work_order": doc_status_card("Work Order", filters, date_field="planned_start_date"),
        "open_work_orders": frappe.db.count(
            "Work Order",
            filters={"company": ["in", filters.companies], "status": ["in", ["Not Started", "In Process"]]},
        ),
        "material_shortage_items": get_material_shortage_count(filters),
    }


def get_material_shortage_count(filters):
    rows = frappe.db.sql(
        """
        select count(distinct wo.name) as cnt
        from `tabWork Order` wo
        where wo.company in %(companies)s
          and wo.status in ('Not Started', 'In Process')
          and exists (
              select 1 from `tabWork Order Item` woi
              where woi.parent = wo.name
                and woi.required_qty > woi.transferred_qty
          )
        """,
        {"companies": filters.companies},
        as_dict=True,
    )
    return flt(rows[0].cnt) if rows else 0
