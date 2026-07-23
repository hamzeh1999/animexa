// Copyright (c) 2026, MIT and contributors
// For license information, please see license.txt

const FARM_PURPOSE_OPTIONS_BY_FARM_TYPE = {
	Breeder: ["Rearing", "Laying", "Day-Old-to-Depletion"],
	Broiler: ["Day-Old-to-Depletion"],
	Layer: ["Rearing", "Laying"],
	Hatchery: ["Hatching"],
};

// Farms saved before Farm Type existed have a Farm Purpose but no Farm Type -
// until Farm Type is actually chosen, show every possible purpose instead of
// narrowing the dropdown down to nothing (which would blank their value out
// visually, even though the stored value is untouched).
const ALL_FARM_PURPOSE_OPTIONS = [...new Set(Object.values(FARM_PURPOSE_OPTIONS_BY_FARM_TYPE).flat())];

frappe.ui.form.on("Farm", {
	refresh(frm) {
		update_farm_purpose_options(frm, { keep_value: true });
	},
	farm_type(frm) {
		update_farm_purpose_options(frm, { keep_value: false });
	},
	view_houses(frm) {
		frappe.set_route("List", "House", { farm: frm.doc.name });
	},
});

function update_farm_purpose_options(frm, { keep_value }) {
	// refresh() re-runs this on every reload/save/focus-regain even though
	// farm_type hasn't changed - skip the redundant set_df_property/refresh_field
	// work when we've already computed the options for this same Farm Type.
	if (frm.__farm_purpose_options_type === frm.doc.farm_type) {
		return;
	}
	frm.__farm_purpose_options_type = frm.doc.farm_type;

	const valid_purposes = frm.doc.farm_type
		? FARM_PURPOSE_OPTIONS_BY_FARM_TYPE[frm.doc.farm_type] || []
		: ALL_FARM_PURPOSE_OPTIONS;

	frm.set_df_property("farm_purpose", "options", ["", ...valid_purposes].join("\n"));
	frm.refresh_field("farm_purpose");

	if (!keep_value && frm.doc.farm_purpose && !valid_purposes.includes(frm.doc.farm_purpose)) {
		frm.set_value("farm_purpose", "");
		frappe.show_alert({
			message: __("Farm Purpose was cleared - it doesn't apply to the selected Farm Type."),
			indicator: "orange",
		});
	}
}
