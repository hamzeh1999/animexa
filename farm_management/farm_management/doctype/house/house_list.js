// Copyright (c) 2026, MIT and contributors
// For license information, please see license.txt

frappe.listview_settings["House"] = {
	get_indicator: function (doc) {
		const status_colors = {
			Ready: "green",
			Occupied: "blue",
			Cleaning: "orange",
			Empty: "grey",
			Inactive: "red",
		};
		return [__(doc.status), status_colors[doc.status], "status,=," + doc.status];
	},
	formatters: {
		housing_model: function (value) {
			const housing_model_colors = {
				"Rear-and-Move": "blue",
				"Day-Old-to-Depletion": "purple",
			};
			const color = housing_model_colors[value] || "grey";
			return `<span class="indicator-pill ${color} ellipsis">
				<span class="ellipsis">${__(value)}</span>
			</span>`;
		},
	},
};
