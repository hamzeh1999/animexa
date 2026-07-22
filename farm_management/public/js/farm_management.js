// frappe-charts (Donut/Pie/Percentage) skips the legend's value <text> node
// whenever a series value is 0 - see legendDot() in the frappe-charts source,
// which only appends that node `if (value)`. That leaves zero-count
// categories (e.g. a status with no Farms) showing a colored dot + label but
// no visible number, which reads as missing data rather than a real zero.
//
// This backfills a "0" next to any legend label that has none, cloning the
// style attributes off another value node already drawn in the same chart so
// it matches positioning/font without hardcoding frappe-charts internals.
(function () {
	function fill_zero_legend_values() {
		document.querySelectorAll(".chart-container svg").forEach(function (svg) {
			var template = svg.querySelector(".legend-dataset-value");
			if (!template) return;

			svg.querySelectorAll("g").forEach(function (group) {
				var label = group.querySelector(".legend-dataset-label");
				if (!label || group.querySelector(".legend-dataset-value")) return;

				var value = template.cloneNode(false);
				value.textContent = "0";
				group.appendChild(value);
			});
		});
	}

	var scheduled = false;
	function schedule() {
		if (scheduled) return;
		scheduled = true;
		requestAnimationFrame(function () {
			scheduled = false;
			fill_zero_legend_values();
		});
	}

	new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
	schedule();
})();
