import frappe


@frappe.whitelist()
def get_pending_health_alerts_card(filters=None):
	"""Custom Number Card source for the Animexa workspace.

	Farm Incident Log is a child table of Farm, so it has no standalone desk
	route to click through to (frappe.router only registers routes for
	doctypes in frappe.boot.user.can_read, which excludes child tables).
	Routing to the "Incident Log Report" Query Report instead of the
	doctype's own List/Report view works around that.
	"""
	count = frappe.db.count("Farm Incident Log", {"closed": 0})
	return {
		"value": count,
		"fieldtype": "Int",
		"route": ["query-report", "Pending Incident Log Report"],
	}
