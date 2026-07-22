import frappe
from frappe import _

STATUSES = ["Ready", "Occupied", "Cleaning", "Empty", "Inactive"]


def execute(filters=None):
	columns = get_columns()
	data = get_data()
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns():
	return [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
		{"label": _("Farms"), "fieldname": "count", "fieldtype": "Int", "width": 100},
	]


def get_data():
	counts = dict(
		frappe.get_all(
			"Farm",
			fields=["status", {"COUNT": "name"}],
			group_by="status",
			as_list=1,
		)
	)
	return [{"status": status, "count": counts.get(status, 0)} for status in STATUSES]


def get_chart(data):
	return {
		"data": {
			"labels": [row["status"] for row in data],
			"datasets": [{"name": "Farms", "values": [row["count"] for row in data]}],
		},
		"type": "donut",
	}
