(function () {
  function fmt(template, data) {
    return String(template || "").replace(/\{(\w+)\}/g, function (m, key) {
      return data[key] != null ? data[key] : m;
    });
  }

  function formatDate(isoDate) {
    var parts = String(isoDate || "").split("-");
    if (parts.length !== 3) return isoDate;
    return parts[2] + "/" + parts[1] + "/" + parts[0];
  }

  window.wireLogPurge = function (opts) {
    var fromEl = document.getElementById(opts.fromId);
    var toEl = document.getElementById(opts.toId);
    var btn = document.getElementById(opts.btnId);
    var msgEl = document.getElementById(opts.msgId);
    var modal = document.getElementById(opts.modalId);
    var bodyEl = document.getElementById(opts.bodyId);
    var confirmBtn = document.getElementById(opts.confirmId);
    var i18n = opts.i18n || {};
    if (!fromEl || !toEl || !btn || !modal || !bodyEl || !confirmBtn) return;

    var pending = null;

    function setMsg(text, kind) {
      if (!msgEl) return;
      if (!text) {
        msgEl.hidden = true;
        msgEl.textContent = "";
        msgEl.className = "log-purge__msg";
        return;
      }
      msgEl.hidden = false;
      msgEl.textContent = text;
      msgEl.className = "log-purge__msg log-purge__msg--" + (kind || "error");
    }

    function closeModal() {
      if (!modal.classList.contains("is-open")) return;
      pending = null;
      modal.classList.remove("is-open");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    }

    function openModal() {
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
    }

    document.querySelectorAll("[data-close-log-purge]").forEach(function (el) {
      if (el.getAttribute("data-close-log-purge") !== opts.modalId) return;
      el.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.classList.contains("is-open")) closeModal();
    });

    btn.addEventListener("click", function () {
      var dateFrom = (fromEl.value || "").trim();
      var dateTo = (toEl.value || "").trim();
      if (!dateFrom || !dateTo) {
        setMsg(i18n.needDates, "error");
        return;
      }
      if (dateFrom > dateTo) {
        setMsg(i18n.invalid, "error");
        return;
      }
      setMsg("");
      btn.disabled = true;
      var params = new URLSearchParams();
      params.set("date_from", dateFrom);
      params.set("date_to", dateTo);
      fetch(opts.countUrl + "?" + params.toString(), {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (body) {
          if (!body || !body.ok) {
            setMsg((body && body.error) || i18n.network, "error");
            return;
          }
          var n = Number(body.count || 0);
          if (!n) {
            setMsg(i18n.none, "error");
            return;
          }
          pending = { date_from: dateFrom, date_to: dateTo, count: n };
          bodyEl.textContent = fmt(i18n.confirmBody, {
            n: n,
            from: formatDate(dateFrom),
            to: formatDate(dateTo),
          });
          openModal();
        })
        .catch(function () {
          setMsg(i18n.network, "error");
        })
        .finally(function () {
          btn.disabled = false;
        });
    });

    confirmBtn.addEventListener("click", function () {
      if (!pending) return;
      confirmBtn.disabled = true;
      fetch(opts.deleteUrl, {
        method: "DELETE",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(pending),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (body) {
          if (!body || !body.ok) {
            closeModal();
            setMsg((body && body.error) || i18n.network, "error");
            return;
          }
          var n = body.deleted || (pending && pending.count) || 0;
          closeModal();
          if (i18n.ok) setMsg(fmt(i18n.ok, { n: n }), "ok");
          if (typeof opts.onDeleted === "function") {
            opts.onDeleted(n);
            return;
          }
          window.location.reload();
        })
        .catch(function () {
          closeModal();
          setMsg(i18n.network, "error");
        })
        .finally(function () {
          confirmBtn.disabled = false;
        });
    });
  };
})();
