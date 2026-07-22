# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from farm_management.farm_management.doctype.farm.farm import (
	get_farm_biosecurity_errors,
	update_farm_house_totals,
	update_farm_status,
)


HOUSING_MODEL_OPTIONS_BY_FARM_TYPE = {
	"Breeder": ["Rear-and-Move", "Day-Old-to-Depletion"],
	"Broiler": ["Day-Old-to-Depletion"],
	"Layer": ["Rear-and-Move", "Day-Old-to-Depletion"],
	"Hatchery": ["Day-Old-to-Depletion"],
}


class House(Document):
	def validate(self):
		self.validate_housing_model()
		self.calculate_capacity()

		if self.status == "Ready":
			errors = []
			if not self.all_in__all_out:
				errors.append("All In / All Out must be checked before status can be Ready.")

			farm = frappe.get_doc("Farm", self.farm)
			errors.extend(get_farm_biosecurity_errors(farm, prefix="Farm "))

			if errors:
				frappe.throw("<br>".join(errors))

	def validate_housing_model(self):
		"""Housing Model choices depend on the linked Farm's farm_type (enforced
		client-side too, in house.js). This is the hard gate for paths that skip
		the client script - Data Import, API, background jobs - so it throws
		instead of silently clearing, unlike the client-side UX.
		"""
		if not self.farm:
			return

		farm_type = frappe.db.get_value("Farm", self.farm, "farm_type")
		if not farm_type:
			return

		valid_models = HOUSING_MODEL_OPTIONS_BY_FARM_TYPE.get(farm_type, [])
		if self.housing_model not in valid_models:
			frappe.throw(
				f"Housing Model '{self.housing_model}' is not valid for a {farm_type} farm. "
				f"Allowed options: {', '.join(valid_models) or 'none'}."
			)

	def calculate_capacity(self):
		"""Male/Female Capacity needs a density standard (birds per m²), and
		House no longer carries one - Parent Stock Standard was removed from
		this DocType because density belongs at the Flock/Production Standard
		level, not House. Until a House-level (or linked) density source
		exists, capacity can't be computed, so this resets it to 0 instead of
		guessing or hardcoding a density.
		"""
		if self.male_capacity or self.female_capacity:
			frappe.msgprint(
				"Male/Female Capacity could not be calculated: no capacity standard is "
				"available at the House level. Capacity has been reset to 0 instead of "
				"keeping an unverified value.",
				indicator="orange",
				title="Capacity Not Calculated",
			)

		self.male_capacity = 0
		self.female_capacity = 0

	def after_insert(self):
		update_farm_status(self.farm)

	def on_update(self):
		update_farm_house_totals(self.farm)
		update_farm_status(self.farm)

		previous = self.get_doc_before_save()
		if previous and previous.farm and previous.farm != self.farm:
			update_farm_house_totals(previous.farm)
			update_farm_status(previous.farm)

	def on_trash(self):
		# Fires before this House's row is deleted, so exclude it explicitly -
		# otherwise the Farm roll-up would still count a House that's on its way out.
		update_farm_status(self.farm, exclude_house=self.name)

	def after_delete(self):
		update_farm_house_totals(self.farm)
