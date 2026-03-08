/**
 * ARIA Shell - Core UI logic for the modernized ARIA platform.
 * Handles HTMX event listeners, JS component re-initialization, 
 * and global UI state.
 */

(function () {
  /**
   * RE-INITIALIZATION LOGIC
   * These plugins must be re-initialized after HTMX swaps dynamic content.
   */
  function initPlugins(container = document) {
    // 1. DataTables
    if (window.jQuery && jQuery.fn.DataTable) {
      $(container).find('table.dataTable:not(.initialized)').each(function() {
        $(this).addClass('initialized').DataTable();
      });
    }

    // 2. Select2
    if (window.jQuery && jQuery.fn.select2) {
      $(container).find('select.select2:not(.initialized)').each(function() {
        $(this).addClass('initialized').select2({
          width: '100%',
          theme: 'bootstrap-5'
        });
      });
    }

    // 3. Tooltips & Popovers (Bootstrap 5)
    const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  /**
   * TOAST SYSTEM
   * Displays non-intrusive notifications.
   */
  window.showToast = function (message, type = "info") {
    const toastContainer = document.getElementById("aria-toast-container");
    if (!toastContainer || !window.htmx) return;

    // Fetch the toast partial via HTMX and append it
    htmx.ajax("GET", `/toast-partial?message=${encodeURIComponent(message)}&type=${type}`, {
      target: "#aria-toast-container",
      swap: "beforeend",
    });
  };

  /**
   * HTMX SECURITY & CONFIGURATION
   */
  function setupHtmx() {
    if (!window.htmx) return;

    // 1. Include CSRF Token in all non-GET requests
    document.addEventListener("htmx:configRequest", (evt) => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
      if (csrfToken) {
        evt.detail.headers["X-CSRFToken"] = csrfToken;
      }
    });

    // 2. Re-initialize plugins after content swap
    document.addEventListener("htmx:afterSwap", (evt) => {
      initPlugins(evt.detail.target);
    });

    // 3. Global Error Handling
    document.addEventListener("htmx:responseError", (evt) => {
      const errorMsg = evt.detail.xhr.responseText || "An unexpected error occurred.";
      window.showToast(errorMsg, "error");
    });
  }

  /**
   * LEGACY COMPATIBILITY
   * Kept for existing announcement logic until fully HTMX-ified.
   */
  function setupLegacyLogic() {
    window.deleteAnnouncement = function (announceId) {
      if (!announceId) return;
      
      const target = document.getElementById("announcement-list");
      if (window.htmx && target) {
        htmx.ajax("POST", "/delete-announcement", {
          target: "#announcement-list",
          swap: "innerHTML",
          values: { AnnounceId: announceId },
        });
      }
    };
  }

  /**
   * INITIALIZATION
   */
  function init() {
    document.body.classList.add("aria-ui");
    setupHtmx();
    setupLegacyLogic();
    initPlugins();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
