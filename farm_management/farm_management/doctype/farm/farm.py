# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


def get_farm_biosecurity_errors(farm, prefix=""):
	errors = []
	if (farm.downtime_days or 0) < 21:
		errors.append(f"{prefix}Downtime Days must be at least 21 (currently {farm.downtime_days or 0}).")
	if not farm.tvc_result:
		errors.append(f"{prefix}TVC Result is required.")
	if farm.salmonella_result != "Negative":
		errors.append(f"{prefix}Salmonella Result must be Negative.")
	return errors


def update_farm_house_totals(farm_name):
	if not farm_name:
		return
	houses = frappe.get_all(
		"House", filters={"farm": farm_name}, fields=["male_capacity", "female_capacity"]
	)
	frappe.db.set_value(
		"Farm",
		farm_name,
		{
			"total_houses": len(houses),
			"total_capacity": sum((h.male_capacity or 0) + (h.female_capacity or 0) for h in houses),
		},
		update_modified=False,
	)


class Farm(Document):
	def autoname(self):
		self.name = self.farm_name

	def validate(self):
		for row in self.visitor_log:
			if row.entry_time and row.exit_time and row.exit_time < row.entry_time:
				frappe.throw(f"Row #{row.idx} in Visitor Log: Exit Time cannot be before Entry Time.")
			if row.previous_farm_visited and row.previous_farm_visited == self.name:
				frappe.throw(f"Row #{row.idx} in Visitor Log: Previous Farm Visited cannot be this same farm.")
			if row.next_farm_to_visit and row.next_farm_to_visit == self.name:
				frappe.throw(f"Row #{row.idx} in Visitor Log: Next Farm to Visit cannot be this same farm.")
			if (
				row.last_contact_with_poultry
				and row.entry_time
				and getdate(row.last_contact_with_poultry) > getdate(row.entry_time)
			):
				frappe.throw(
					f"Row #{row.idx} in Visitor Log: Last Contact with Poultry cannot be after Entry Time."
				)

		for row in self.water_quality_tests:
			if row.ph is not None and not (0 <= row.ph <= 14):
				frappe.throw(f"Row #{row.idx} in Water Quality Tests: pH must be between 0 and 14.")

		for row in self.incident_log:
			if row.closed and not row.corrective_action:
				frappe.throw(f"Row #{row.idx} in Incident Log: Corrective Action is required when Closed is checked.")

		if self.cleaning_start_date and self.ready_date:
			self.downtime_days = (getdate(self.ready_date) - getdate(self.cleaning_start_date)).days
		else:
			self.downtime_days = 0

		if self.status == "Ready":
			errors = get_farm_biosecurity_errors(self)
			if not any(
				row.pass_fail == "Pass" and row.tvc is not None and row.ph is not None
				for row in self.water_quality_tests
			):
				errors.append("At least one Water Quality Test with a Pass result and valid TVC/pH values is required.")
			if any(row.severity == "Critical" and not row.closed for row in self.incident_log):
				errors.append("Cannot set status to Ready while there are open Critical incidents.")

			if errors:
				frappe.throw("<br>".join(errors))

	def on_update(self):
		update_farm_house_totals(self.name)
