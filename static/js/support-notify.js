(function () {
  var badge = document.getElementById("nav-support-unread");
  if (!badge) return;

  var userMeta = document.querySelector('meta[name="support-notify-user"]');
  var adminMeta = document.querySelector('meta[name="support-notify-admin"]');
  var agentMeta = document.querySelector('meta[name="support-notify-is-agent"]');
  var toastUser = (userMeta && userMeta.getAttribute("content")) || "New support message";
  var toastAdmin = (adminMeta && adminMeta.getAttribute("content")) || "New user message";
  var isAgent = agentMeta && agentMeta.getAttribute("content") === "1";

  var lastCount = -1;
  var toastEl = null;
  var toastTimer = null;
  var pollMs = 8000;

  function supportHref() {
    return isAgent ? "/admin/chats-soporte" : "/admin/soporte";
  }

  function onSupportPage() {
    var path = window.location.pathname || "";
    return path.indexOf("/admin/soporte") !== -1 || path.indexOf("/admin/chats-soporte") !== -1;
  }

  function formatBadge(count) {
    return count > 9 ? "9+" : String(count);
  }

  function updateBadge(count) {
    if (!badge) return;
    if (count > 0) {
      badge.textContent = formatBadge(count);
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  function ensureToast() {
    if (toastEl) return toastEl;
    toastEl = document.createElement("a");
    toastEl.className = "support-toast";
    toastEl.setAttribute("role", "status");
    toastEl.setAttribute("aria-live", "polite");
    document.body.appendChild(toastEl);
    return toastEl;
  }

  function showToast(message) {
    var el = ensureToast();
    el.textContent = message;
    el.href = supportHref();
    el.hidden = false;
    el.classList.add("support-toast--visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.classList.remove("support-toast--visible");
      setTimeout(function () {
        el.hidden = true;
      }, 280);
    }, 4500);
  }

  function maybeNotify(count) {
    if (lastCount < 0) {
      lastCount = count;
      updateBadge(count);
      return;
    }
    if (count > lastCount) {
      if (!onSupportPage() || document.hidden) {
        showToast(isAgent ? toastAdmin : toastUser);
      }
      if (document.hidden && "Notification" in window && Notification.permission === "granted") {
        try {
          new Notification(isAgent ? toastAdmin : toastUser, {
            tag: "support-chat",
            renotify: true,
          });
        } catch (e) {}
      }
    }
    lastCount = count;
    updateBadge(count);
  }

  function poll() {
    fetch("/admin/api/soporte/unread", { headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) return null;
        return r.json();
      })
      .then(function (data) {
        if (!data || !data.ok) return;
        maybeNotify(parseInt(data.count, 10) || 0);
      })
      .catch(function () {});
  }

  if ("Notification" in window && Notification.permission === "default") {
    document.addEventListener(
      "click",
      function requestNotifyOnce() {
        Notification.requestPermission().catch(function () {});
        document.removeEventListener("click", requestNotifyOnce);
      },
      { once: true }
    );
  }

  poll();
  setInterval(poll, pollMs);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) poll();
  });
})();
