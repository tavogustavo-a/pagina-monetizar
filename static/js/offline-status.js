(function () {
  var offlineMeta = document.querySelector('meta[name="offline-banner-offline"]');
  var onlineMeta = document.querySelector('meta[name="offline-banner-online"]');
  var offlineText = (offlineMeta && offlineMeta.getAttribute("content")) || "Sin conexión";
  var onlineText = (onlineMeta && onlineMeta.getAttribute("content")) || "Conexión restaurada";
  var banner = null;
  var hideTimer = null;

  function ensureBanner() {
    if (banner) return banner;
    banner = document.createElement("div");
    banner.className = "offline-status";
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");
    document.body.appendChild(banner);
    return banner;
  }

  function showBanner(message, mode) {
    var el = ensureBanner();
    el.textContent = message;
    el.classList.remove("offline-status--offline", "offline-status--online");
    el.classList.add(mode === "online" ? "offline-status--online" : "offline-status--offline");
    el.hidden = false;
  }

  function hideBanner(delay) {
    if (!banner) return;
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () {
      if (banner) banner.hidden = true;
    }, delay || 0);
  }

  function onOffline() {
    clearTimeout(hideTimer);
    showBanner(offlineText, "offline");
  }

  function onOnline() {
    showBanner(onlineText, "online");
    hideBanner(2600);
  }

  window.addEventListener("offline", onOffline);
  window.addEventListener("online", onOnline);

  if (!navigator.onLine) {
    onOffline();
  }
})();
