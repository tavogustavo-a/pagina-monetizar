(function () {
  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var pickerTriggers = {};

  function releasePickerFocus(modal, returnFocusEl) {
    var active = document.activeElement;
    if (!active || !modal || !modal.contains(active)) return;
    if (returnFocusEl && typeof returnFocusEl.focus === "function") {
      returnFocusEl.focus();
    } else {
      active.blur();
    }
  }

  function blurPickerFocus(modal) {
    if (!modal) return;
    var active = document.activeElement;
    if (active && modal.contains(active)) {
      active.blur();
    }
  }

  function closePickerModal(modalId, returnFocusEl) {
    var modal = document.getElementById(modalId);
    if (!modal) return;
    var trigger = returnFocusEl || pickerTriggers[modalId] || null;
    releasePickerFocus(modal, trigger);
    blurPickerFocus(modal);
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    if (trigger) trigger.setAttribute("aria-expanded", "false");
    delete pickerTriggers[modalId];
  }

  function closeAllPickerModals() {
    document.querySelectorAll(".stats-picker-modal.is-open").forEach(function (modal) {
      closePickerModal(modal.id, pickerTriggers[modal.id]);
    });
  }

  function openPickerModal(modalId, openBtn) {
    closeAllPickerModals();
    var modal = document.getElementById(modalId);
    if (!modal || !openBtn) return;
    pickerTriggers[modalId] = openBtn;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    openBtn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function renderDefaultOption(item, selected, extraHtml) {
    return (
      '<li role="option" tabindex="0" class="stats-picker-modal__option' +
      (selected ? " is-selected" : "") +
      '" data-picker-id="' +
      escapeHtml(item.id) +
      '" aria-selected="' +
      (selected ? "true" : "false") +
      '"><span class="stats-picker-modal__option-main">' +
      (extraHtml || "") +
      '<span class="stats-picker-modal__name">' +
      escapeHtml(item.name || "") +
      "</span></span></li>"
    );
  }

  function submitStatsForm(form) {
    if (!form) return;
    if (typeof window.statsAjaxNavigate === "function") {
      window.statsAjaxNavigate(form);
      return;
    }
    form.submit();
  }

  function wireStatsPicker(cfg) {
    var modal = document.getElementById(cfg.modalId);
    var openBtn = document.getElementById(cfg.openId);
    var hiddenInput = document.getElementById(cfg.hiddenId);
    var listEl = document.getElementById(cfg.listId);
    var searchEl = document.getElementById(cfg.searchId);
    var searchClear = document.getElementById(cfg.searchClearId);
    var emptyEl = cfg.emptyId ? document.getElementById(cfg.emptyId) : null;
    var loadingEl = cfg.loadingId ? document.getElementById(cfg.loadingId) : null;
    if (!modal || !openBtn || !hiddenInput || !listEl) return;
    if (openBtn.dataset.statsPickerWired === "1") return;
    openBtn.dataset.statsPickerWired = "1";

    var choices = (cfg.choices || []).slice();
    var selectedId = cfg.selectedId || "";
    var searchTimer = null;

    function choiceById(id) {
      return choices.find(function (c) {
        return String(c.id) === String(id);
      }) || null;
    }

    function filterChoices(query) {
      var q = (query || "").trim().toLowerCase();
      if (!q) return choices.slice();
      return choices.filter(function (c) {
        var hay = (cfg.searchText ? cfg.searchText(c) : c.name || "").toLowerCase();
        return hay.indexOf(q) !== -1;
      });
    }

    function renderList(items) {
      if (!items.length) {
        listEl.innerHTML = "";
        if (emptyEl) emptyEl.hidden = false;
        return;
      }
      if (emptyEl) emptyEl.hidden = true;
      listEl.innerHTML = items
        .map(function (c) {
          return cfg.renderOption(c, String(c.id) === String(selectedId));
        })
        .join("");
    }

    function updateTrigger() {
      if (cfg.updateTrigger) cfg.updateTrigger(choiceById(selectedId), selectedId);
      openBtn.classList.toggle("has-selection", !!selectedId || cfg.alwaysSelected);
    }

    function refreshChoices() {
      if (!cfg.fetchChoices) {
        renderList(filterChoices(searchEl ? searchEl.value : ""));
        updateTrigger();
        return Promise.resolve();
      }
      if (loadingEl) loadingEl.hidden = false;
      if (emptyEl) emptyEl.hidden = true;
      listEl.innerHTML = "";
      return cfg
        .fetchChoices()
        .then(function (next) {
          if (next) choices = next;
          renderList(filterChoices(searchEl ? searchEl.value : ""));
          updateTrigger();
        })
        .catch(function () {
          renderList(filterChoices(searchEl ? searchEl.value : ""));
        })
        .finally(function () {
          if (loadingEl) loadingEl.hidden = true;
        });
    }

    function pick(id) {
      if (String(id) === String(selectedId)) {
        closePickerModal(cfg.modalId, openBtn);
        return;
      }
      selectedId = id;
      hiddenInput.value = id;
      updateTrigger();
      closePickerModal(cfg.modalId, openBtn);
      if (cfg.onPick) cfg.onPick(choiceById(selectedId), selectedId);
      else if (cfg.form) submitStatsForm(cfg.form);
    }

    openBtn.addEventListener("click", function () {
      if (modal.classList.contains("is-open")) {
        closePickerModal(cfg.modalId, openBtn);
        return;
      }
      if (searchEl) {
        searchEl.value = "";
        if (searchClear) searchClear.hidden = true;
      }
      openPickerModal(cfg.modalId, openBtn);
      refreshChoices().then(function () {
        if (searchEl) searchEl.focus();
      });
    });

    listEl.addEventListener("click", function (e) {
      var opt = e.target.closest(".stats-picker-modal__option");
      if (!opt) return;
      pick(opt.getAttribute("data-picker-id") || "");
    });

    listEl.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var opt = e.target.closest(".stats-picker-modal__option");
      if (!opt) return;
      e.preventDefault();
      pick(opt.getAttribute("data-picker-id") || "");
    });

    if (searchEl && window.wireAjaxSearch) {
      window.wireAjaxSearch(
        searchEl,
        searchClear,
        function () {
          renderList(filterChoices(searchEl.value));
        },
        180
      );
    } else if (searchEl) {
      searchEl.addEventListener("input", function () {
        if (searchClear) searchClear.hidden = !searchEl.value.trim();
        clearTimeout(searchTimer);
        searchTimer = setTimeout(function () {
          renderList(filterChoices(searchEl.value));
        }, 180);
      });
    }

    if (searchClear && searchEl && !window.wireAjaxSearch) {
      searchClear.addEventListener("click", function () {
        searchEl.value = "";
        searchClear.hidden = true;
        renderList(filterChoices(""));
        searchEl.focus();
      });
    }

    renderList(filterChoices(""));
    updateTrigger();
  }

  function bindStatsPickerCloseHandlers() {
    if (bindStatsPickerCloseHandlers.bound) return;
    bindStatsPickerCloseHandlers.bound = true;
    document.querySelectorAll("[data-close-stats-picker]").forEach(function (el) {
      el.addEventListener("click", function () {
        var modalId = el.getAttribute("data-close-stats-picker") || "";
        closePickerModal(modalId, pickerTriggers[modalId]);
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAllPickerModals();
    });
  }

  window.initStatsPickers = function (config) {
    bindStatsPickerCloseHandlers();

    if (config.platform) {
      var platformIconEl = document.getElementById("stats-platform-label-icon");
      var platformTextEl = document.getElementById("stats-platform-label-text");
      wireStatsPicker({
        modalId: "stats-platform-modal",
        openId: "stats-platform-open",
        hiddenId: "stats-platform-id",
        listId: "stats-platform-list",
        searchId: "stats-platform-search",
        searchClearId: "stats-platform-search-clear",
        emptyId: "stats-platform-empty",
        form: document.getElementById("stats-filters-form"),
        choices: config.platform.choices || [],
        selectedId: config.platform.selectedId || "all",
        alwaysSelected: true,
        onPick: function () {
          var accountInput = document.getElementById("stats-account-id");
          if (accountInput) accountInput.value = "";
          var accountLabel = document.querySelector("#stats-account-label .stats-picker__text");
          if (accountLabel && config.account) {
            accountLabel.textContent = config.account.pickLabel;
          }
          var accountOpen = document.getElementById("stats-account-open");
          if (accountOpen) accountOpen.classList.remove("has-selection");
          var consultFlag = document.getElementById("stats-consult-flag");
          if (consultFlag) consultFlag.value = "";
        },
        searchText: function (c) {
          return (c.name || "") + " " + (c.id || "") + " " + (c.icon || "");
        },
        renderOption: function (c, selected) {
          return renderDefaultOption(c, selected);
        },
        updateTrigger: function (picked) {
          if (platformTextEl) {
            platformTextEl.textContent = picked ? picked.name : config.platform.pickLabel;
          }
          if (platformIconEl) {
            if (picked && picked.icon) {
              platformIconEl.textContent = picked.icon;
              platformIconEl.hidden = false;
            } else {
              platformIconEl.textContent = "";
              platformIconEl.hidden = true;
            }
          }
        },
      });
    }

    if (config.account) {
      var accountLabelEl = document.querySelector("#stats-account-label .stats-picker__text");
      wireStatsPicker({
        modalId: "stats-account-modal",
        openId: "stats-account-open",
        hiddenId: "stats-account-id",
        listId: "stats-account-list",
        searchId: "stats-account-search",
        searchClearId: "stats-account-search-clear",
        emptyId: "stats-account-empty",
        loadingId: "stats-account-loading",
        form: document.getElementById("stats-filters-form"),
        choices: config.account.choices || [],
        selectedId: config.account.selectedId || "",
        searchText: function (c) {
          return (c.name || "") + " " + (c.platform || "") + " " + (c.kind || "");
        },
        fetchChoices: function () {
          var platformId = document.getElementById("stats-platform-id");
          var params = new URLSearchParams();
          params.set("platform", platformId ? platformId.value || "all" : "all");
          return fetch("/admin/api/stats-filter-choices?" + params.toString(), {
            credentials: "same-origin",
            headers: { Accept: "application/json" },
          })
            .then(function (r) {
              return r.json();
            })
            .then(function (body) {
              return body && body.ok ? body.choices || [] : null;
            });
        },
        renderOption: function (c, selected) {
          var kind = c.kind === "group" ? config.account.kindGroup : config.account.kindAccount;
          var meta = '<span class="stats-picker-modal__kind">' + escapeHtml(kind) + "</span>";
          return renderDefaultOption(c, selected, meta);
        },
        updateTrigger: function (picked) {
          if (accountLabelEl) {
            accountLabelEl.textContent = picked ? picked.name : config.account.pickLabel;
          }
        },
        onPick: function () {
          var consultFlag = document.getElementById("stats-consult-flag");
          if (consultFlag) consultFlag.value = "";
        },
      });
    }

    if (config.video) {
      var videoLabelEl = document.querySelector("#stats-video-label .stats-picker__text");
      wireStatsPicker({
        modalId: "stats-video-modal",
        openId: "stats-video-open",
        hiddenId: "stats-video-id",
        listId: "stats-video-list",
        searchId: "stats-video-search",
        searchClearId: "stats-video-search-clear",
        emptyId: "stats-video-empty",
        form: document.getElementById("stats-video-filter-form"),
        choices: config.video.choices || [],
        selectedId: config.video.selectedId || "",
        alwaysSelected: true,
        searchText: function (c) {
          return c.name || "";
        },
        renderOption: function (c, selected) {
          return renderDefaultOption(c, selected, "");
        },
        updateTrigger: function (picked) {
          if (videoLabelEl) {
            videoLabelEl.textContent = picked ? picked.name : config.video.pickLabel;
          }
        },
        onPick: function () {
          submitStatsForm(document.getElementById("stats-video-filter-form"));
        },
      });
    }
  };

  window.initPubAccountPicker = function (config) {
    if (!config) return;
    bindStatsPickerCloseHandlers();
    var accountLabelEl = document.querySelector("#" + config.openId + " .stats-picker__text");
    wireStatsPicker({
      modalId: config.modalId,
      openId: config.openId,
      hiddenId: config.hiddenId,
      listId: config.listId,
      searchId: config.searchId,
      searchClearId: config.searchClearId,
      emptyId: config.emptyId,
      choices: config.choices || [],
      selectedId: config.selectedId || "",
      searchText: function (c) {
        return (c.name || "") + " " + (c.platform || "") + " " + (c.kind || "");
      },
      renderOption: function (c, selected) {
        var kind =
          c.kind === "group" ? config.kindGroup || "Group" : config.kindAccount || "Account";
        var meta = '<span class="stats-picker-modal__kind">' + escapeHtml(kind) + "</span>";
        return renderDefaultOption(c, selected, meta);
      },
      updateTrigger: function (picked) {
        if (accountLabelEl) {
          accountLabelEl.textContent = picked ? picked.name : config.pickLabel || "";
        }
      },
      onPick: config.onPick,
    });
  };
})();
