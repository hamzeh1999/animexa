# Copyright (c) 2026, MIT and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from farm_management.farm_management.doctype.farm.farm import (
	get_farm_biosecurity_errors,
	update_farm_house_totals,
)


class House(Document):
	def validate(self):
		self.calculate_capacity()

		if self.status == "Ready":
			errors = []
			if not self.all_in__all_out:
				errors.append("All In / All Out must be checked before status can be Ready.")

			farm = frappe.get_doc("Farm", self.farm)
			errors.extend(get_farm_biosecurity_errors(farm, prefix="Farm "))

			if errors:
				frappe.throw("<br>".join(errors))

	def calculate_capacity(self):
		"""Recalculate male_capacity/female_capacity from Floor Area x density.

		Density values must come from the linked Parent Stock Standard record.
		No such density data exists in the system yet (the Link doesn't even point
		to a doctype that has density fields), so this reports that clearly and
		resets capacity to 0 instead of guessing or hardcoding a density.
		"""
		reason = None
		male_capacity = 0
		female_capacity = 0

		if not self.parent_stock_standard:
			reason = "Parent Stock Standard is not set on this House."
		else:
			target_doctype = frappe.get_meta(self.doctype).get_field("parent_stock_standard").options
			target_meta = frappe.get_meta(target_doctype)
			if not (target_meta.has_field("male_density") and target_meta.has_field("female_density")):
				reason = (
					f"The linked Parent Stock Standard doctype ('{target_doctype}') does not "
					"have male_density/female_density fields defined."
				)
			else:
				standard = frappe.get_doc(target_doctype, self.parent_stock_standard)
				male_density = standard.get("male_density")
				female_density = standard.get("female_density")
				if male_density is None or female_density is None:
					reason = "The linked Parent Stock Standard record has no density values set."
				else:
					floor_area = self.get("floor_area_m²") or 0
					male_capacity = round(floor_area * male_density)
					female_capacity = round(floor_area * female_density)

		if reason and (self.male_capacity or self.female_capacity):
			frappe.msgprint(
				f"Male/Female Capacity could not be calculated: {reason} "
				"Capacity has been reset to 0 instead of keeping an unverified value.",
				indicator="orange",
				title="Capacity Not Calculated",
			)

		self.male_capacity = male_capacity
		self.female_capacity = female_capacity

	def on_update(self):
		update_farm_house_totals(self.farm)

		previous = self.get_doc_before_save()
		if previous and previous.farm and previous.farm != self.farm:
			update_farm_house_totals(previous.farm)

	def after_delete(self):
		update_farm_house_totals(self.farm)
