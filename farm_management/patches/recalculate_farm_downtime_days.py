# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import date_diff


def execute():
	"""Downtime Days used to be calculated from Cleaning Start Date instead of
	Cleaning End Date - existing Farms still hold values computed under that
	wrong formula, and the field is now read-only so nothing will fix them
	short of a real edit. Recalculate them here with the corrected formula.

	Uses frappe.db.set_value (not doc.save()) so a Farm with unrelated data
	issues (e.g. missing mandatory fields on a legacy record) can't abort
	the migration - Farms with an inconsistent date order are left untouched
	for manual review instead of being guessed at.
	"""
	farms = frappe.get_all(
		"Farm", fields=["name", "cleaning_start_date", "cleaning_end_date", "ready_date"]
	)

	skipped = []
	for farm in farms:
		if (
			farm.cleaning_start_date
			and farm.cleaning_end_date
			and farm.cleaning_end_date < farm.cleaning_start_date
		):
			skipped.append(farm.name)
			continue

		if farm.cleaning_end_date and farm.ready_date:
			if farm.ready_date < farm.cleaning_end_date:
				skipped.append(farm.name)
				continue
			downtime_days = date_diff(farm.ready_date, farm.cleaning_end_date)
		else:
			downtime_days = 0

		frappe.db.set_value("Farm", farm.name, "downtime_days", downtime_days, update_modified=False)

	if skipped:
		frappe.log_error(
			title="Farm Downtime Days recalculation skipped",
			message=(
				"These Farms have Cleaning Start/End/Ready dates out of chronological "
				"order and were left untouched - review and correct their dates "
				f"manually: {', '.join(skipped)}"
			),
		)
