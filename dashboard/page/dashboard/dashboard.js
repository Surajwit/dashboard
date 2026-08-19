frappe.pages["dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Overview Dashboard",
		single_column: true,
	});
	new Dashboard(page);
};

class Dashboard {
	constructor(page) {
		this.page = page;
		this.edit_mode = false;
		this.drag_id = null;
		this.state = { financial_year: null, from_date: null, to_date: null, companies: [], branch: null, cost_center: null };
		this.layout = [];
		this.data = {};
		this.catalog = [];
		this.init();
	}

	async init() {
		this.$root = $("<div class='dashboard'></div>").appendTo(this.page.main);
		this.render_shell();
		this.page.set_primary_action("Refresh", () => this.load_data(), "refresh");
		this.add_menu_actions();
		await Promise.all([this.load_filter_options(), this.load_catalog(), this.load_layout()]);
		this.render_filters();
		this.render_layout();
		await this.load_data();
	}

	add_menu_actions() {
		this.page.add_menu_item("Customize Dashboard", () => this.toggle_edit_mode());
		this.page.add_menu_item("Reset Dashboard", () => this.reset_layout());
	}

	render_shell() {
		this.$root.html(`
			<div class="nd-shell">
				<aside class="nd-sidebar">
					<div class="nd-brand"><div class="nd-brand-mark">N</div><div><strong>Dashboard</strong><span>ERPNext Dashboard</span></div></div>
					<nav class="nd-nav">
						<a class="active" href="#"><span>▣</span>Overview</a>
						<a href="/app/purchase-order"><span>🛒</span>Purchase</a>
						<a href="/app/sales-order"><span>🛒</span>Sales</a>
						<a href="/app/account"><span>▤</span>Accounting</a>
						<a href="/app/supplier"><span>♙</span>Supplier</a>
						<a href="/app/customer"><span>♧</span>Customer</a>
						<a href="/app/employee"><span>♙</span>Employee</a>
						<a href="/app/purchase-invoice"><span>₹</span>Payables</a>
						<a href="/app/sales-invoice"><span>₹</span>Receivables</a>
						<a href="/app/accounting-ledger"><span>⌁</span>Income &amp; Expenses</a>
						<a href="/app/query-report"><span>▥</span>Reports</a>
						<a href="/app/system-settings"><span>⚙</span>Settings</a>
					</nav>
					<div class="nd-quick-filter"><h4>Quick Filters</h4><div data-region="quick-filters"></div></div>
				</aside>
				<main class="nd-main">
					<header class="nd-header">
						<div><div class="nd-menu">☰</div><div><h1>Overview Dashboard</h1><p>Real-time overview of your business operations</p></div></div>
						<div class="nd-header-actions"><button class="nd-icon-btn nd-customize">⚙</button><span class="nd-user">Administrator⌄</span></div>
					</header>
					<section class="nd-toolbar"><div data-region="filters"></div><div class="nd-toolbar-actions"><button class="nd-btn nd-btn-primary nd-apply">Apply Filters</button><button class="nd-btn nd-btn-ghost nd-save" hidden>Save Layout</button><button class="nd-btn nd-btn-ghost nd-add" hidden>+ Add Widget</button></div></section>
					<div class="nd-edit-hint" hidden>Customize mode: drag cards to reorder, use the width control to resize, or remove/add widgets. Save when finished.</div>
					<div class="nd-content"><div class="nd-section-label">TRANSACTION / DOCUMENT OVERVIEW</div><div class="nd-grid" data-region="dashboard-grid"></div></div>
				</main>
			</div>`);
		this.$root.on("click", ".nd-customize", () => this.toggle_edit_mode());
		this.$root.on("click", ".nd-apply", () => this.read_filters_and_load());
		this.$root.on("click", ".nd-save", () => this.save_layout());
		this.$root.on("click", ".nd-add", () => this.add_widget());
	}

	async load_filter_options() {
		const r = await frappe.call("dashboard.api.dashboard.get_filter_options");
		this.options = r.message || {};
		const fy = (this.options.fiscal_years || [])[0];
		if (fy) {
			this.state.financial_year = fy.name;
			this.state.from_date = fy.year_start_date;
			this.state.to_date = fy.year_end_date;
		}
		if (!this.state.companies.length && (this.options.companies || []).length) this.state.companies = [this.options.companies[0]];
	}

	async load_catalog() {
		const r = await frappe.call("dashboard.api.dashboard.get_widget_catalog");
		this.catalog = r.message || [];
	}

	async load_layout() {
		const r = await frappe.call("dashboard.api.dashboard.get_dashboard_layout");
		this.layout = r.message || [];
	}

	render_filters() {
		const o = this.options || {};
		const fy = (o.fiscal_years || []).map(f => `<option value="${esc(f.name)}" data-from="${esc(f.year_start_date)}" data-to="${esc(f.year_end_date)}" ${f.name === this.state.financial_year ? "selected" : ""}>${esc(f.name)}</option>`).join("");
		const companies = (o.companies || []).map(c => `<option value="${esc(c)}" ${this.state.companies.includes(c) ? "selected" : ""}>${esc(c)}</option>`).join("");
		this.$root.find('[data-region="filters"]').html(`
			<div class="nd-filter"><label>Financial Year</label><select data-filter="financial_year">${fy}</select></div>
			<div class="nd-filter nd-date"><label>Date Range</label><div><input type="date" data-filter="from_date" value="${esc(this.state.from_date || "")}"><span>–</span><input type="date" data-filter="to_date" value="${esc(this.state.to_date || "")}"></div></div>
			<div class="nd-filter"><label>Company</label><select multiple data-filter="companies">${companies}</select></div>
			<div class="nd-filter"><label>Branch</label><select data-filter="branch"><option value="">All</option>${(o.branches || []).map(x => `<option value="${esc(x)}" ${x === this.state.branch ? "selected" : ""}>${esc(x)}</option>`).join("")}</select></div>
			<div class="nd-filter"><label>Cost Center</label><select data-filter="cost_center"><option value="">All</option>${(o.cost_centers || []).map(x => `<option value="${esc(x)}" ${x === this.state.cost_center ? "selected" : ""}>${esc(x)}</option>`).join("")}</select></div>`);
		this.$root.find('[data-filter="financial_year"]').on("change", e => {
			const opt = e.target.selectedOptions[0];
			this.$root.find('[data-filter="from_date"]').val(opt?.dataset.from || "");
			this.$root.find('[data-filter="to_date"]').val(opt?.dataset.to || "");
		});
		this.render_quick_filters();
	}

	render_quick_filters() {
		const o = this.options || {};
		this.$root.find('[data-region="quick-filters"]').html(`
			<label>Company</label><select data-qf="company">${(o.companies || []).map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join("")}</select>
			<label>Branch</label><select data-qf="branch"><option value="">All</option>${(o.branches || []).map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join("")}</select>
			<label>Cost Center</label><select data-qf="cost_center"><option value="">All</option>${(o.cost_centers || []).map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join("")}</select>`);
	}

	read_filters_and_load() {
		const root = this.$root;
		this.state.financial_year = root.find('[data-filter="financial_year"]').val();
		this.state.from_date = root.find('[data-filter="from_date"]').val();
		this.state.to_date = root.find('[data-filter="to_date"]').val();
		this.state.companies = root.find('[data-filter="companies"]').val() || [];
		this.state.branch = root.find('[data-filter="branch"]').val() || null;
		this.state.cost_center = root.find('[data-filter="cost_center"]').val() || null;
		this.load_data();
	}

	async load_data() {
		frappe.dom.freeze("Loading dashboard...");
		try {
			const r = await frappe.call({ method: "dashboard.api.dashboard.get_dashboard_data", args: this.state });
			this.data = r.message || {};
			this.render_layout();
		} catch (e) {
			frappe.msgprint({ title: "Dashboard Error", indicator: "red", message: "The dashboard could not load. Check Error Log for details." });
		} finally {
			frappe.dom.unfreeze();
		}
	}

	render_layout() {
		const $grid = this.$root.find('[data-region="dashboard-grid"]').empty();
		this.layout.forEach(item => {
			const $item = $(`<div class="nd-widget" data-id="${esc(item.id)}" style="--nd-col:${item.col || 3}"></div>`);
			$item.html(`<div class="nd-widget-head"><h3>${esc(item.title)}</h3><div class="nd-widget-actions" hidden><select class="nd-width"><option value="2">2/12</option><option value="3">3/12</option><option value="4">4/12</option><option value="6">6/12</option><option value="8">8/12</option><option value="12">12/12</option></select><button class="nd-remove">×</button></div></div><div class="nd-widget-body"></div>`);
			$item.find(".nd-width").val(String(item.col || 3)).on("change", e => { item.col = Number(e.target.value); $item.css("--nd-col", item.col); });
			$item.find(".nd-remove").on("click", () => { this.layout = this.layout.filter(x => x.id !== item.id); this.render_layout(); });
			if (this.edit_mode) {
				$item.attr("draggable", "true");
				$item.find(".nd-widget-actions").prop("hidden", false);
				$item.on("dragstart", () => { this.drag_id = item.id; $item.addClass("dragging"); });
				$item.on("dragend", () => { this.drag_id = null; $item.removeClass("dragging"); });
				$item.on("dragover", e => { e.preventDefault(); $item.addClass("drag-over"); });
				$item.on("dragleave", () => $item.removeClass("drag-over"));
				$item.on("drop", e => { e.preventDefault(); $item.removeClass("drag-over"); this.reorder(this.drag_id, item.id); });
			}
			$grid.append($item);
			this.render_widget($item.find(".nd-widget-body"), item);
		});
	}

	reorder(source, target) {
		if (!source || source === target) return;
		const from = this.layout.findIndex(x => x.id === source);
		const to = this.layout.findIndex(x => x.id === target);
		if (from < 0 || to < 0) return;
		const [moved] = this.layout.splice(from, 1);
		this.layout.splice(to, 0, moved);
		this.render_layout();
	}

	toggle_edit_mode() {
		this.edit_mode = !this.edit_mode;
		this.$root.find(".nd-edit-hint").prop("hidden", !this.edit_mode);
		this.$root.find(".nd-save, .nd-add").prop("hidden", !this.edit_mode);
		this.$root.toggleClass("is-editing", this.edit_mode);
		this.render_layout();
	}

	async save_layout() {
		await frappe.call({ method: "dashboard.api.dashboard.save_dashboard_layout", args: { layout: JSON.stringify(this.layout) } });
		frappe.show_alert({ message: "Dashboard layout saved", indicator: "green" });
		this.toggle_edit_mode();
	}

	async reset_layout() {
		const confirmed = await new Promise(resolve => frappe.confirm("Reset your dashboard to the default layout?", () => resolve(true), () => resolve(false)));
		if (!confirmed) return;
		const r = await frappe.call("dashboard.api.dashboard.reset_dashboard_layout");
		this.layout = r.message || [];
		this.render_layout();
	}

	add_widget() {
		const options = (this.catalog || []).filter(x => !this.layout.some(y => y.id === x.id));
		if (!options.length) { frappe.msgprint("All available widgets are already on your dashboard."); return; }
		const d = new frappe.ui.Dialog({
			title: "Add Dashboard Widget",
			fields: [{ fieldname: "widget", label: "Widget", fieldtype: "Select", options: options.map(x => x.id + " — " + x.title).join("\n"), reqd: 1 }],
			primary_action_label: "Add",
			primary_action: values => {
				const id = values.widget.split(" — ")[0];
				const item = options.find(x => x.id === id);
				this.layout.push({ ...item });
				d.hide();
				this.render_layout();
			},
		});
		d.show();
	}

	render_widget($body, item) {
		try {
			const d = this.data;
			const A = d.accounting || {}, P = d.purchase || {}, S = d.sales || {}, H = d.hr || {};
			switch (item.id) {
				case "purchase_order": return this.render_document($body, P.purchase_order, "purchase", "Purchase Order");
				case "purchase_invoice": return this.render_document($body, P.purchase_invoice, "purchase", "Purchase Invoice");
				case "payment_request": return this.render_document($body, A.payment_request, "payment", "Payment Request");
				case "sales_order": return this.render_document($body, S.sales_order, "sales", "Sales Order");
				case "sales_invoice": return this.render_document($body, S.sales_invoice, "sales", "Sales Invoice");
				case "journal_entry": return this.render_document($body, A.journal_entry, "voucher", "Voucher Entry");
				case "suppliers": return this.render_master($body, P.active_suppliers, "Active Suppliers", "supplier");
				case "customers": return this.render_master($body, S.active_customers, "Active Customers", "customer");
				case "employees": return this.render_master($body, H.active_employees, "Active Employees", "employee");
				case "payables": return this.render_amount($body, A.payables, "Payables", "down");
				case "receivables": return this.render_amount($body, A.receivables, "Receivables", "up");
				case "income_expense": return this.render_income_expense($body, A);
				case "payables_ageing": return this.render_donut($body, "Payables Ageing", A.payables_ageing || [], A.payables?.total || 0);
				case "receivables_ageing": return this.render_donut($body, "Receivables Ageing", A.receivables_ageing || [], A.receivables?.total || 0);
				case "monthly_trend": return this.render_line($body, A.monthly_trend || []);
				case "top_suppliers": return this.render_ranking($body, "Top 5 Suppliers", A.top_suppliers || []);
				case "top_customers": return this.render_ranking($body, "Top 5 Customers", A.top_customers || []);
				case "document_status_summary": return this.render_donut($body, "Document Status Summary", d.document_status_summary?.by_status || [], d.document_status_summary?.total || 0, true);
				case "recent_activities": return this.render_recent($body, d.recent_activities || []);
				case "cash_position": return this.render_cash($body, A.cash_position || {});
				case "expenses_by_category": return this.render_expenses($body, A.expenses_by_category || []);
				case "quick_shortcuts": return this.render_shortcuts($body);
				case "stock_snapshot": return this.render_snapshot($body, "Stock", d.stock || {});
				case "manufacturing_snapshot": return this.render_snapshot($body, "Manufacturing", d.manufacturing || {});
				case "crm_snapshot": return this.render_snapshot($body, "CRM", d.crm || {});
				case "asset_snapshot": return this.render_snapshot($body, "Assets", d.assets || {});
			}
		} catch (e) {
			$body.html(`<div class="nd-empty nd-error">Unable to render this widget.</div>`);
		}
	}

	render_document($b, card, theme, label) {
		if (!card) return $b.html(`<div class="nd-empty">No data available</div>`);
		const statuses = (card.by_status || []).slice(0, 4).map((x, i) => `<li><span><i class="status-dot dot-${i}"></i>${esc(x.status)}</span><strong>${x.count}</strong></li>`).join("");
		$b.html(`<div class="nd-doc-card"><div class="nd-doc-icon ${theme}">${iconFor(theme)}</div><div class="nd-doc-main"><div class="nd-eyebrow">${esc(label)}</div><div class="nd-big-number">${fmtNumber(card.total)}</div><ul class="nd-status-list">${statuses}</ul><a href="/app/${routeFor(card.doctype)}">View Details →</a></div></div>`);
	}

	render_master($b, value, label, theme) { $b.html(`<div class="nd-master-card"><div class="nd-master-icon ${theme}">${iconFor(theme)}</div><div><div class="nd-eyebrow">${esc(label)}</div><div class="nd-big-number">${fmtNumber(value || 0)}</div><div class="nd-muted">Active ${label}</div><a href="/app/${theme}">View Details →</a></div></div>`); }

	render_amount($b, value, label, direction) { const v = value || {}; $b.html(`<div class="nd-amount-card ${direction}"><div class="nd-amount-icon">₹</div><div><div class="nd-eyebrow">${esc(label)}</div><div class="nd-big-number">${money(v.total)}</div><div class="nd-overdue">Overdue ${money(v.overdue)}</div><a href="/app/${label.toLowerCase() === "payables" ? "purchase-invoice" : "sales-invoice"}">View Details →</a></div></div>`); }

	render_income_expense($b, a) { $b.html(`<div class="nd-finance-grid"><div class="finance-box income"><span>Total Income</span><strong>${money(a.income?.total)}</strong><small>Vs Last Year <b>${pct(a.income?.yoy_pct)}</b></small><em>Operating ${money(a.income?.operating)} · Other ${money(a.income?.other)}</em></div><div class="finance-box expense"><span>Total Expenses</span><strong>${money(a.expense?.total)}</strong><small>Vs Last Year <b>${pct(a.expense?.yoy_pct)}</b></small><em>Operating ${money(a.expense?.operating)} · Other ${money(a.expense?.other)}</em></div><div class="finance-box surplus"><span>Net Surplus</span><strong>${money(a.net_surplus?.total)}</strong><small>Vs Last Year <b>${pct(a.net_surplus?.yoy_pct)}</b></small><em>Income less Expenses</em></div></div>`); }

	render_donut($b, title, rows, total, status=false) { const id = "chart-" + Math.random().toString(36).slice(2); $b.html(`<div class="nd-chart-wrap"><div class="nd-chart-title">${esc(title)}</div><div class="nd-chart-area"><div id="${id}"></div><div class="nd-center-total">${status ? "Total" : "₹"}<strong>${status ? fmtNumber(total) : shortMoney(total)}</strong></div></div><ul class="nd-legend">${rows.map((x,i)=>`<li><span><i class="legend-dot c${i}"></i>${esc(x.label || x.status)}</span><span>${status ? fmtNumber(x.count) : shortMoney(x.amount)} ${x.pct != null ? `<small>${x.pct}%</small>` : ""}</span></li>`).join("")}</ul></div>`); if (rows.length && window.frappe?.Chart) { new frappe.Chart(`#${id}`, { data:{labels:rows.map(x=>x.label||x.status),datasets:[{values:rows.map(x=>x.amount != null ? x.amount : x.count)}]}, type:"donut", height:190, colors:["#43AE45","#1E73EF","#FC970E","#734CD3","#1CA8AB","#E43938"] }); } }

	render_line($b, rows) { const id="chart-"+Math.random().toString(36).slice(2); $b.html(`<div class="nd-chart-wrap"><div class="nd-chart-title">Monthly Trend <small>(This Financial Year)</small></div><div id="${id}"></div></div>`); if (rows.length && window.frappe?.Chart) new frappe.Chart(`#${id}`, {data:{labels:rows.map(x=>x.month),datasets:[{name:"Income",values:rows.map(x=>x.income)},{name:"Expenses",values:rows.map(x=>x.expense)},{name:"Net Surplus",values:rows.map(x=>x.net_surplus)}]},type:"line",height:220,colors:["#43AE45","#E43938","#1E73EF"]}); }

	render_ranking($b, title, rows) { $b.html(`<div class="nd-table-wrap"><div class="nd-chart-title">${esc(title)} <small>(By Amount)</small></div><table><thead><tr><th>#</th><th>Party</th><th>Amount</th><th>Overdue</th></tr></thead><tbody>${rows.map((x,i)=>`<tr><td>${i+1}</td><td>${esc(x.party)}</td><td>${money(x.amount)}</td><td>${money(x.overdue)}</td></tr>`).join("")}</tbody></table><a class="nd-table-link">View All →</a></div>`); }

	render_recent($b, rows) { $b.html(`<div class="nd-list-wrap"><div class="nd-chart-title">Recent Activities</div><ul class="nd-activity">${rows.slice(0,6).map(x=>`<li><i></i><span>${esc(x.doctype)} <b>${esc(x.name)}</b> ${esc(x.status).toLowerCase()}</span><time>${timeOnly(x.timestamp)}</time></li>`).join("")}</ul><a>View All Activities →</a></div>`); }

	render_cash($b, cash) { $b.html(`<div class="nd-list-wrap"><div class="nd-chart-title">Cash Position <small>(Bank Accounts)</small></div><div class="nd-cash-total">${money(cash.total)}<small>Across ${fmtNumber((cash.accounts||[]).length)} Bank/Cash Accounts</small></div><ul class="nd-mini-list">${(cash.accounts||[]).slice(0,5).map(x=>`<li><span>${esc(x.account)}</span><b>${money(x.balance)}</b></li>`).join("")}</ul><a>View All Bank Accounts →</a></div>`); }

	render_expenses($b, rows) { const id="chart-"+Math.random().toString(36).slice(2); $b.html(`<div class="nd-chart-wrap"><div class="nd-chart-title">Expenses by Category <small>(This FY)</small></div><div class="nd-chart-area compact"><div id="${id}"></div></div><ul class="nd-legend">${rows.slice(0,6).map((x,i)=>`<li><span><i class="legend-dot c${i}"></i>${esc(x.category)}</span><span>${money(x.amount)} <small>${x.pct}%</small></span></li>`).join("")}</ul></div>`); if (rows.length && window.frappe?.Chart) new frappe.Chart(`#${id}`, {data:{labels:rows.map(x=>x.category),datasets:[{values:rows.map(x=>x.amount)}]},type:"donut",height:160,colors:["#1E73EF","#43AE45","#FC970E","#E43938","#734CD3","#1CA8AB"]}); }

	render_shortcuts($b) { const items=[["New Purchase Order","purchase-order","🛒"],["New Sales Order","sales-order","🛒"],["New Payment Request","payment-request","▣"],["New Sales Invoice","sales-invoice","▤"],["New Voucher Entry","journal-entry","▤"],["Bank Reconciliation","bank-reconciliation","₹"],["Reports","query-report","▥"],["Chart of Accounts","account","◉"],["View All Masters","list","☷"]]; $b.html(`<div class="nd-shortcuts"><div class="nd-chart-title">Quick Shortcuts</div><div class="shortcut-grid">${items.map(x=>`<a href="/app/${x[1]}"><i>${x[2]}</i><span>${x[0]}</span></a>`).join("")}</div></div>`); }

	render_snapshot($b, title, data) { const entries=[]; Object.entries(data).forEach(([k,v])=>{ if(typeof v === "number") entries.push([k.replaceAll("_"," "),v]); }); $b.html(`<div class="nd-snapshot"><div class="nd-chart-title">${esc(title)} Snapshot</div>${entries.slice(0,5).map(x=>`<div><span>${esc(x[0])}</span><strong>${fmtNumber(x[1])}</strong></div>`).join("") || `<div class="nd-empty">No snapshot data</div>`}</div>`); }
}

function esc(v) { return String(v ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c])); }
function fmtNumber(v) { return Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 }); }
function money(v) { try { return format_currency(Number(v || 0)); } catch(e) { return "₹ " + Number(v || 0).toLocaleString("en-IN", {maximumFractionDigits:2}); } }
function shortMoney(v) { return Number(v || 0).toLocaleString("en-IN", {maximumFractionDigits:1}); }
function pct(v) { const n=Number(v||0); return (n>=0?"▲ ":"▼ ") + Math.abs(n).toFixed(2) + "%"; }
function timeOnly(v) { if(!v) return ""; return frappe.datetime.str_to_user(v).split(" ").slice(1).join(" "); }
function routeFor(dt) { return String(dt || "").toLowerCase().replace(/ /g,"-"); }
function iconFor(theme) { return {purchase:"🛒",sales:"🛒",payment:"▣",voucher:"▤",supplier:"♙",customer:"♧",employee:"♙"}[theme] || "◉"; }
