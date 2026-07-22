(function () {
    if (window.__anxLoaderInit) return;
    window.__anxLoaderInit = true;

    let activeReqs = 0;
    let showTimer = null;
    let visibleSince = 0;

    const SHOW_DELAY_MS = 120;
    const MIN_VISIBLE_MS = 180;

    function getOverlay() {
        let ov = document.getElementById("animexa-global-overlay");
        if (!ov && document.body) {
            ov = document.createElement("div");
            ov.id = "animexa-global-overlay";
            ov.style.position = "fixed";
            ov.style.inset = "0";
            ov.style.zIndex = "999999";
            ov.style.display = "none";
            ov.style.flexDirection = "column";
            ov.style.alignItems = "center";
            ov.style.justifyContent = "center";
            ov.style.pointerEvents = "none";
            ov.innerHTML = `
                <div class="anx-core">
                    <div class="anx-pulse"></div>
                    <div class="anx-orbit"></div>
                    <div class="anx-egg"><div class="anx-scan"></div></div>
                </div>
                <div class="anx-text">
                  
                </div>
            `;
            document.body.appendChild(ov);
        }
        return ov;
    }

    function destroyNative() {
        let els = document.querySelectorAll("#freeze, .freeze-container, .frappe-spinner, #spinner, .spinner, .ajax-spinner, .progress-spinner");
        els.forEach(e => e.remove());
    }

    function setOverlayActive(isActive) {
        let ov = getOverlay();
        if (!ov) return;
        if (isActive) {
            ov.classList.add("is-active");
            ov.style.display = "flex";
            ov.style.pointerEvents = "auto";
            visibleSince = Date.now();
        } else {
            ov.classList.remove("is-active");
            ov.style.pointerEvents = "none";
            ov.style.display = "none";
        }
    }

    function scheduleShow() {
        if (showTimer) return;
        showTimer = window.setTimeout(function () {
            showTimer = null;
            if (activeReqs > 0) {
                setOverlayActive(true);
            }
        }, SHOW_DELAY_MS);
    }

    function clearScheduledShow() {
        if (!showTimer) return;
        window.clearTimeout(showTimer);
        showTimer = null;
    }

    function requestHide() {
        clearScheduledShow();

        let ov = document.getElementById("animexa-global-overlay");
        if (!ov || !ov.classList.contains("is-active")) {
            setOverlayActive(false);
            return;
        }

        const elapsed = Date.now() - visibleSince;
        const wait = Math.max(0, MIN_VISIBLE_MS - elapsed);

        if (wait > 0) {
            window.setTimeout(function () {
                if (activeReqs === 0) {
                    setOverlayActive(false);
                }
            }, wait);
        } else {
            setOverlayActive(false);
        }
    }

    function showLoader() {
        activeReqs++;
        destroyNative();
        scheduleShow();
    }

    function hideLoader() {
        activeReqs = Math.max(0, activeReqs - 1);
        destroyNative();
        if (activeReqs === 0) {
            requestHide();
        }
    }

    function concludeReq(xhr) {
        if (!xhr || xhr.__anxDone) return;
        xhr.__anxDone = true;
        hideLoader();
    }

    if (typeof $ !== "undefined") {
        $(document).ready(function () {
            getOverlay();
            destroyNative();
            requestHide();
        });

        $(window).on("load", function () {
            destroyNative();
            requestHide();
        });

        $(document).ajaxSend(function (e, xhr) {
            if (xhr) xhr.__anxDone = false;
            showLoader();
        });

        $(document).ajaxComplete(function (e, xhr) {
            concludeReq(xhr);
        });

        $(document).ajaxError(function (e, xhr) {
            concludeReq(xhr);
        });
    }

    if (window.frappe) {
        let origFreeze = frappe.freeze;
        let origUnfreeze = frappe.unfreeze;

        frappe.freeze = function (msg) {
            showLoader();
            return origFreeze ? origFreeze.call(this, msg) : undefined;
        };

        frappe.unfreeze = function () {
            hideLoader();
            return origUnfreeze ? origUnfreeze.call(this) : undefined;
        };
    }

    if (typeof MutationObserver !== "undefined" && document.body) {
        const cleanupObserver = new MutationObserver(function () {
            if (activeReqs > 0) {
                destroyNative();
            }
        });
        cleanupObserver.observe(document.body, { childList: true, subtree: true });
    }
})();