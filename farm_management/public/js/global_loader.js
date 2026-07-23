(function () {
    if (window.__anxLoaderInit) return;
    window.__anxLoaderInit = true;

    function getOverlay() {
        let ov = document.getElementById("animexa-global-overlay");
        if (!ov && document.body) {
            ov = document.createElement("div");
            ov.id = "animexa-global-overlay";
            ov.innerHTML = '<div class="anx-spinner"></div><div class="anx-loading-text">Loading...</div>';
            document.body.appendChild(ov);
        }
        return ov;
    }

    function showOverlay() {
        const ov = getOverlay();
        if (ov) ov.classList.add("is-active");
    }

    function hideOverlay() {
        const ov = document.getElementById("animexa-global-overlay");
        if (ov) ov.classList.remove("is-active");
    }

    if (window.frappe) {
        const origFreeze = frappe.freeze;
        const origUnfreeze = frappe.unfreeze;

        frappe.freeze = function (msg) {
            showOverlay();
            return origFreeze ? origFreeze.call(this, msg) : undefined;
        };

        frappe.unfreeze = function () {
            hideOverlay();
            return origUnfreeze ? origUnfreeze.call(this) : undefined;
        };
    }
})();
