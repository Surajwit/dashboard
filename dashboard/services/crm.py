import frappe

from dashboard.services.common import doc_status_card


def get_widgets(filters):
    opportunity = doc_status_card("Opportunity", filters, date_field="transaction_date")
    won = frappe.db.count(
        "Opportunity",
        filters={
            "company": ["in", filters.companies],
            "status": "Converted",
            "transaction_date": ["between", [filters.from_date, filters.to_date]],
        },
    )
    return {
        "opportunity": opportunity,
        "open_opportunities": frappe.db.count(
            "Opportunity",
            filters={"company": ["in", filters.companies], "status": ["in", ["Open", "Replied"]]},
        ),
        "conversion_rate_pct": round(won / (opportunity["total"] or 1) * 100, 1),
    }
