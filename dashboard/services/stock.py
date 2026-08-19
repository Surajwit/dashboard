import frappe
from frappe.utils import flt

from dashboard.services.common import doc_status_card, master_count


def get_widgets(filters):
    return {
        "stock_entry": doc_status_card("Stock Entry", filters, date_field="posting_date"),
        "active_items": master_count("Item", {"disabled": 0, "is_stock_item": 1}),
        "stock_value": get_stock_value(filters),
        "low_stock_items": get_low_stock_count(filters),
    }


def get_stock_value(filters):
    rows = frappe.db.sql(
        """
        select sum(sle.stock_value_difference) as value
        from `tabStock Ledger Entry` sle
        where sle.company in %(companies)s
          and sle.posting_date <= %(as_of)s
          and sle.is_cancelled = 0
        """,
        {"companies": filters.companies, "as_of": filters.to_date},
        as_dict=True,
    )
    return flt(rows[0].value) if rows and rows[0].value else 0


def get_low_stock_count(filters):
    rows = frappe.db.sql(
        """
        select count(distinct b.item_code) as cnt
        from `tabBin` b
        inner join `tabItem Reorder` ir on ir.parent = b.item_code
        where b.warehouse = ir.warehouse
          and b.actual_qty <= ir.warehouse_reorder_level
        """,
        as_dict=True,
    )
    return flt(rows[0].cnt) if rows else 0
