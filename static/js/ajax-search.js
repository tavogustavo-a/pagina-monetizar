(function () {
  window.wireAjaxSearch = function (input, clearBtn, onSearch, delayMs) {
    if (!input || typeof onSearch !== "function") return;
    var delay = delayMs == null ? 320 : delayMs;
    var timer = null;

    function runNow() {
      onSearch(input.value.trim());
    }

    input.addEventListener("input", function () {
      if (clearBtn) clearBtn.hidden = !input.value.trim();
      clearTimeout(timer);
      timer = setTimeout(runNow, delay);
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        input.value = "";
        clearBtn.hidden = true;
        onSearch("");
        input.focus();
      });
    }
  };

  window.wireAjaxSelectSearch = function (selectEl, onSearch, delayMs) {
    if (!selectEl || typeof onSearch !== "function") return;
    var delay = delayMs == null ? 180 : delayMs;
    var timer = null;
    selectEl.addEventListener("change", function () {
      clearTimeout(timer);
      timer = setTimeout(onSearch, delay);
    });
  };
})();
