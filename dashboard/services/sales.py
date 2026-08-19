from dashboard.services.common import doc_status_card, master_count


def get_widgets(filters):
    return {
        "sales_order": doc_status_card("Sales Order", filters),
        "sales_invoice": doc_status_card("Sales Invoice", filters),
        "delivery_note": doc_status_card("Delivery Note", filters),
        "active_customers": master_count("Customer", {"disabled": 0}),
    }
