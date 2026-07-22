(function () {
	if (window.__globalLoaderInit) return;
	window.__globalLoaderInit = true;

	var activeRequests = 0;

	function ensureOverlay() {
		var overlay = document.getElementById("global-loader-overlay");
		if (!overlay && document.body) {
			overlay = document.createElement("div");
			overlay.id = "global-loader-overlay";
			overlay.innerHTML = '<div class="global-loader-ring" aria-hidden="true"></div>';
			document.body.appendChild(overlay);
		}
		return overlay;
	}

	function nukeNativeSpinners() {
		$("#freeze, .freeze-container, .frappe-spinner, #spinner, .spinner, .ajax-spinner, .progress-spinner, .splash, #splash, .splash-logo, .centered-app-logo, img[src*='frappe'], img[src*='erpnext']").remove();
	}

	function syncOverlay() {
		var overlay = ensureOverlay();
		if (!overlay) return;
		overlay.classList.toggle("is-active", activeRequests > 0);
	}

	function showLoader() {
		activeRequests += 1;
		nukeNativeSpinners();
		syncOverlay();
	}

	function hideLoader() {
		activeRequests = Math.max(0, activeRequests - 1);
		nukeNativeSpinners();
		syncOverlay();
	}

	function finishRequest(jqXHR) {
		if (!jqXHR || jqXHR.__globalLoaderDone) return;
		jqXHR.__globalLoaderDone = true;
		hideLoader();
	}

	$(document).ready(function () {
		ensureOverlay();
		nukeNativeSpinners();
		syncOverlay();
	});

	$(window).on("load", function () {
		nukeNativeSpinners();
		syncOverlay();
	});

	$(document).ajaxSend(function (_event, jqXHR) {
		if (jqXHR) jqXHR.__globalLoaderDone = false;
		showLoader();
	});

	$(document).ajaxComplete(function (_event, jqXHR) {
		finishRequest(jqXHR);
	});

	$(document).ajaxError(function (_event, jqXHR) {
		finishRequest(jqXHR);
	});

	if (window.frappe) {
		var originalFreeze = frappe.freeze;
		var originalUnfreeze = frappe.unfreeze;

		frappe.freeze = function (msg) {
			showLoader();
			return originalFreeze ? originalFreeze.call(this, msg) : undefined;
		};

		frappe.unfreeze = function () {
			hideLoader();
			return originalUnfreeze ? originalUnfreeze.call(this) : undefined;
		};
	}

	setInterval(nukeNativeSpinners, 1000);
})();