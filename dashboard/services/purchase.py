from dashboard.services.common import doc_status_card, master_count


def get_widgets(filters):
    return {
        "purchase_order": doc_status_card("Purchase Order", filters),
        "purchase_invoice": doc_status_card("Purchase Invoice", filters),
        "purchase_receipt": doc_status_card("Purchase Receipt", filters),
        "active_suppliers": master_count("Supplier", {"disabled": 0}),
    }
