import hashlib
import json

import frappe

DEFAULT_TTL = 5 * 60


def _cache_key(widget_name, filters_dict):
    payload = json.dumps(filters_dict, sort_keys=True, default=str)
    digest = hashlib.md5(payload.encode()).hexdigest()  # noqa: S324
    return f"dashboard::{widget_name}::{digest}"


def get_or_set(widget_name, filters_dict, compute_fn, ttl=DEFAULT_TTL):
    key = _cache_key(widget_name, filters_dict)
    cached = frappe.cache().get_value(key)
    if cached is not None:
        return cached
    value = compute_fn()
    frappe.cache().set_value(key, value, expires_in_sec=ttl)
    return value


def clear_dashboard_cache():
    # Dashboard keys are filter-hashed, so the safest low-cost invalidation is
    # a namespace version key used by future extensions. Current requests have
    # a short TTL and remain safe if old values expire naturally.
    frappe.cache().set_value("dashboard::last_clear", frappe.utils.now_datetime())


def warm_dashboard_cache():
    from dashboard.api.dashboard import get_dashboard_data

    for company in frappe.get_list("Company", pluck="name"):
        try:
            get_dashboard_data(companies=[company])
        except Exception:
            frappe.log_error(
                title="dashboard: cache warm failed",
                message=frappe.get_traceback(),
            )
