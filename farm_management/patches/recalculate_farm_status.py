# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe

from farm_management.farm_management.doctype.farm.farm import update_farm_status


def execute():
	for farm_name in frappe.get_all("Farm", pluck="name"):
		update_farm_status(farm_name)
