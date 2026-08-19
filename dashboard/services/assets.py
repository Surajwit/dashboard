import frappe
from frappe.utils import add_days, flt


def get_widgets(filters):
    return {
        "total_asset_value": get_total_asset_value(filters),
        "depreciation_this_period": get_depreciation_this_period(filters),
        "assets_due_for_maintenance": get_upcoming_maintenance_count(filters),
    }


def get_total_asset_value(filters):
    rows = frappe.db.sql(
        """
        select sum(a.value_after_depreciation) as value
        from `tabAsset` a
        where a.company in %(companies)s
          and a.status in ('Submitted', 'Partially Depreciated')
          and a.docstatus = 1
        """,
        {"companies": filters.companies},
        as_dict=True,
    )
    return flt(rows[0].value) if rows and rows[0].value else 0


def get_depreciation_this_period(filters):
    rows = frappe.db.sql(
        """
        select sum(ds.depreciation_amount) as amount
        from `tabDepreciation Schedule` ds
        inner join `tabAsset` a on a.name = ds.parent
        where a.company in %(companies)s
          and ds.schedule_date between %(from_date)s and %(to_date)s
        """,
        {"companies": filters.companies, "from_date": filters.from_date, "to_date": filters.to_date},
        as_dict=True,
    )
    return flt(rows[0].amount) if rows and rows[0].amount else 0


def get_upcoming_maintenance_count(filters, lookahead_days=30):
    return frappe.db.count(
        "Asset Maintenance Task",
        filters={"next_due_date": ["between", [filters.to_date, add_days(filters.to_date, lookahead_days)]]},
    )
