// Copyright (c) 2026, MIT and contributors
// For license information, please see license.txt

const HOUSING_MODEL_OPTIONS_BY_FARM_TYPE = {
	Breeder: ["Rear-and-Move", "Day-Old-to-Depletion"],
	Broiler: ["Day-Old-to-Depletion"],
	Layer: ["Rear-and-Move", "Day-Old-to-Depletion"],
	Hatchery: ["Day-Old-to-Depletion"],
};

// Houses on a Farm with no farm_type set yet (or no Farm selected at all) get
// every possible option instead of nothing - narrowing to zero would blank an
// existing value out visually without actually touching the stored data.
const ALL_HOUSING_MODEL_OPTIONS = [...new Set(Object.values(HOUSING_MODEL_OPTIONS_BY_FARM_TYPE).flat())];

frappe.ui.form.on("House", {
	refresh(frm) {
		apply_housing_model_filter(frm, { keep_value: true });
	},
	farm(frm) {
		apply_housing_model_filter(frm, { keep_value: false });
	},
});

function apply_housing_model_filter(frm, { keep_value }) {
	if (!frm.doc.farm) {
		set_housing_model_options(frm, ALL_HOUSING_MODEL_OPTIONS, keep_value);
		return;
	}

	frappe.db.get_value("Farm", frm.doc.farm, "farm_type").then(({ message }) => {
		const farm_type = message && message.farm_type;
		const valid_models = farm_type
			? HOUSING_MODEL_OPTIONS_BY_FARM_TYPE[farm_type] || []
			: ALL_HOUSING_MODEL_OPTIONS;
		set_housing_model_options(frm, valid_models, keep_value);
	});
}

function set_housing_model_options(frm, valid_models, keep_value) {
	frm.set_df_property("housing_model", "options", ["", ...valid_models].join("\n"));
	frm.refresh_field("housing_model");

	if (!keep_value && frm.doc.housing_model && !valid_models.includes(frm.doc.housing_model)) {
		frm.set_value("housing_model", "");
		frappe.show_alert({
			message: __("Housing Model was cleared - please select a valid Housing Model for this Farm."),
			indicator: "orange",
		});
	}
}
