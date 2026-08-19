from . import __version__ as app_version

app_name = "dashboard"
app_title = "Dashboard"
app_publisher = "Surajwit"
app_description = "Configurable overview dashboard for ERPNext"
app_email = ""
app_license = "MIT"

scheduler_events = {
    "cron": {
        "*/15 * * * *": [
            "dashboard.utils.cache.warm_dashboard_cache"
        ]
    }
}
