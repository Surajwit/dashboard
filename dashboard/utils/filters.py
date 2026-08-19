import frappe
from frappe.utils import getdate, get_first_day, get_last_day, nowdate


class DashboardFilters:
    def __init__(self, financial_year=None, from_date=None, to_date=None, companies=None, branch=None, cost_center=None):
        self.financial_year = financial_year
        self.from_date, self.to_date = self._resolve_date_range(financial_year, from_date, to_date)
        self.companies = self._resolve_companies(companies)
        self.branch = branch if branch and branch != "All" else None
        self.cost_center = cost_center if cost_center and cost_center != "All" else None

    def _resolve_date_range(self, financial_year, from_date, to_date):
        if from_date and to_date:
            return getdate(from_date), getdate(to_date)
        if financial_year:
            fy = frappe.db.get_value("Fiscal Year", financial_year, ["year_start_date", "year_end_date"], as_dict=True)
            if fy:
                return fy.year_start_date, fy.year_end_date
        try:
            fy_name = frappe.defaults.get_user_default("fiscal_year") or frappe.db.get_default("fiscal_year")
            fy = frappe.db.get_value("Fiscal Year", fy_name, ["year_start_date", "year_end_date"], as_dict=True)
            if fy:
                return fy.year_start_date, fy.year_end_date
        except Exception:
            pass
        today = getdate(nowdate())
        return get_first_day(today), get_last_day(today)

    def _resolve_companies(self, companies):
        allowed = frappe.get_list("Company", pluck="name")
        if companies:
            if isinstance(companies, str):
                companies = [companies]
            requested = [c for c in companies if c in allowed]
            if requested:
                return requested
        default_company = frappe.defaults.get_user_default("company")
        if default_company and default_company in allowed:
            return [default_company]
        return allowed

    def gl_conditions(self, doc_alias="gl"):
        conditions = [
            f"{doc_alias}.company in %(companies)s",
            f"{doc_alias}.posting_date between %(from_date)s and %(to_date)s",
            f"{doc_alias}.is_cancelled = 0",
        ]
        params = {"companies": self.companies, "from_date": self.from_date, "to_date": self.to_date}
        gl_meta = frappe.get_meta("GL Entry")
        if self.cost_center and gl_meta.has_field("cost_center"):
            conditions.append(f"{doc_alias}.cost_center = %(cost_center)s")
            params["cost_center"] = self.cost_center
        if self.branch and gl_meta.has_field("branch"):
            conditions.append(f"{doc_alias}.branch = %(branch)s")
            params["branch"] = self.branch
        return " and ".join(conditions), params

    def doc_filters(self, doctype, date_field="posting_date"):
        meta = frappe.get_meta(doctype)
        actual_date = date_field if meta.has_field(date_field) else "posting_date"
        if not meta.has_field(actual_date):
            actual_date = "modified"
        filters = {actual_date: ["between", [self.from_date, self.to_date]]}
        if meta.has_field("company"):
            filters["company"] = ["in", self.companies]
        if self.cost_center and meta.has_field("cost_center"):
            filters["cost_center"] = self.cost_center
        if self.branch and meta.has_field("branch"):
            filters["branch"] = self.branch
        return filters

    def as_dict(self):
        return {
            "financial_year": self.financial_year,
            "from_date": str(self.from_date),
            "to_date": str(self.to_date),
            "companies": self.companies,
            "branch": self.branch,
            "cost_center": self.cost_center,
        }
