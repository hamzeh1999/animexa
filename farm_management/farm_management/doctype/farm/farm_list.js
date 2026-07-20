// Copyright (c) 2026, MIT and contributors
// For license information, please see license.txt

frappe.listview_settings["Farm"] = {
	get_indicator: function (doc) {
		const status_colors = {
			Ready: "green",
			Occupied: "blue",
			Cleaning: "orange",
			Empty: "grey",
			Inactive: "red",
		};

		return [
			__(doc.status),
			status_colors[doc.status] || "grey",
			"status,=," + doc.status,
		];
	},

	formatters: {
		farm_purpose: function (value) {
			const farm_purpose_colors = {
				"Day-Old-to-Depletion": "purple",
				"Laying": "green",
				"Rearing": "blue",
			};

			const color = farm_purpose_colors[value] || "grey";

			return `<span class="indicator-pill ${color} ellipsis">
				<span class="ellipsis">${__(value)}</span>
			</span>`;
		},
	},
};