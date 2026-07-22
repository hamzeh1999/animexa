# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate


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


def compute_farm_status(house_statuses):
	"""Roll up a Farm's status from a list of its Houses' statuses.

	Priority order:
	1. Any House Occupied     -> Occupied
	2. Any House Cleaning     -> Cleaning
	3. All Houses Ready       -> Ready
	4. All Houses Empty       -> Empty
	5. No Houses / mixed      -> Inactive
	"""
	statuses = [status for status in house_statuses if status]
	if not statuses:
		return "Inactive"
	if "Occupied" in statuses:
		return "Occupied"
	if "Cleaning" in statuses:
		return "Cleaning"
	if all(status == "Ready" for status in statuses):
		return "Ready"
	if all(status == "Empty" for status in statuses):
		return "Empty"
	return "Inactive"


def get_farm_status(farm_name, exclude_house=None):
	"""Compute what a Farm's status should be right now, from its Houses.

	exclude_house lets on_trash recompute as if a House already gone from the
	Farm, since House.on_trash fires before that House's row is deleted.
	"""
	filters = {"farm": farm_name}
	if exclude_house:
		filters["name"] = ["!=", exclude_house]
	house_statuses = frappe.get_all("House", filters=filters, pluck="status")
	return compute_farm_status(house_statuses)


FARM_PURPOSE_OPTIONS_BY_FARM_TYPE = {
	"Breeder": ["Rearing", "Laying", "Day-Old-to-Depletion"],
	"Broiler": ["Day-Old-to-Depletion"],
	"Layer": ["Rearing", "Laying"],
	"Hatchery": ["Hatching"],
}


def update_farm_status(farm_name, exclude_house=None):
	"""Recalculate and persist Farm.status from the status of its Houses.

	Writes with frappe.db.set_value rather than doc.save(), so this never
	re-enters Farm/House controller hooks and can't cause recursive updates.
	"""
	if not farm_name:
		return
	new_status = get_farm_status(farm_name, exclude_house=exclude_house)
	if frappe.db.get_value("Farm", farm_name, "status") != new_status:
		frappe.db.set_value("Farm", farm_name, "status", new_status, update_modified=False)


class Farm(Document):
	def autoname(self):
		self.name = self.farm_name

	def validate(self):
		# Farm.status is a roll-up of its Houses, not a manually entered value -
		# recompute it here too so it self-heals even if something wrote to it
		# outside of update_farm_status (e.g. Data Import, bulk edit).
		self.status = get_farm_status(self.name)

		if self.farm_type != "Breeder":
			self.breeder_level = None

		# Farm Purpose choices depend on Farm Type (enforced client-side too, in
		# farm.js). Only clear it once farm_type is actually set to something -
		# farms created before farm_type existed still have a farm_purpose with
		# no farm_type yet, and that legacy value shouldn't be wiped out just
		# because they get saved for an unrelated field edit.
		if self.farm_type:
			valid_purposes = FARM_PURPOSE_OPTIONS_BY_FARM_TYPE.get(self.farm_type, [])
			if self.farm_purpose and self.farm_purpose not in valid_purposes:
				self.farm_purpose = None

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

		if (
			self.cleaning_start_date
			and self.cleaning_end_date
			and getdate(self.cleaning_end_date) < getdate(self.cleaning_start_date)
		):
			frappe.throw("Cleaning End Date cannot be before Cleaning Start Date.")

		if (
			self.cleaning_end_date
			and self.ready_date
			and getdate(self.ready_date) < getdate(self.cleaning_end_date)
		):
			frappe.throw("Ready Date cannot be before Cleaning End Date.")

		# Downtime Days is the biosecurity rest period after cleaning finishes,
		# not from when cleaning started - a Farm mid-cleaning hasn't begun its
		# downtime clock yet.
		if self.cleaning_end_date and self.ready_date:
			self.downtime_days = date_diff(self.ready_date, self.cleaning_end_date)
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
