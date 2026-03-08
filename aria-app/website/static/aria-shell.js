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
      $(container).find('table.dataTable, table.table').each(function() {
        const $table = $(this);
        // Only initialize if not already a DataTable and not already processed by us
        if (!$.fn.DataTable.isDataTable(this) && !this.hasAttribute('data-aria-initialized')) {
          this.setAttribute('data-aria-initialized', 'true');
          $table.DataTable({
            responsive: true,
            pageLength: 10
          });
        }
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
   * NAVIGATION LOGIC
   * Handles active state tracking and navigation behaviors.
   */
  function updateActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      }
    });
  }

  /**
   * ROOM DISCOVERY & CALENDAR SYNC
   */
  window.selectRoom = function (roomId, type) {
    // 1. UI Highlight
    document.querySelectorAll('.aria-room-card').forEach(c => c.classList.remove('active'));
    const activeCard = document.querySelector(`.aria-room-card[data-room-id="${roomId}"]`);
    if (activeCard) activeCard.classList.add('active');

    // 2. Sync with hidden legacy selectors for FullCalendar
    const selectorId = (type === 'r') ? "#nroomSelector" : "#eroomSelector";
    const selector = document.querySelector(selectorId);
    if (selector) {
      selector.value = roomId;
      selector.dispatchEvent(new Event('change'));
    }

    // 3. Pre-fill all booking modals
    document.querySelectorAll('select[name="roomSelect"]').forEach(select => {
      select.value = roomId;
    });
    
    console.log(`[ARIA Discovery] Selected room ${roomId} (type: ${type})`);
  };

  /**
   * INITIALIZATION
   */
  function processLegacyFlashes() {
    const flashes = document.querySelectorAll("#legacy-flash-messages .flash-data");
    flashes.forEach((flash) => {
      const message = flash.getAttribute("data-message");
      const category = flash.getAttribute("data-category");
      window.showToast(message, category);
    });
  }

  function init() {
    document.body.classList.add("aria-ui");
    setupHtmx();
    setupLegacyLogic();
    initPlugins();
    processLegacyFlashes();
    updateActiveNavLink();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
