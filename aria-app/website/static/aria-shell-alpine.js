/**
 * ARIA Shell (Alpine.js Edition)
 * Modern client-side orchestration for ARIA using Alpine.js and HTMX.
 */

document.addEventListener('alpine:init', () => {
  // 1. Toast Store for Reactive Notifications
  Alpine.store('toasts', {
    items: [],
    counter: 0,

    add(message, type = 'info', timeout = 5000) {
      const id = ++this.counter;
      const toast = { id, message, type, visible: true };
      this.items.push(toast);

      if (timeout > 0) {
        setTimeout(() => {
          this.remove(id);
        }, timeout);
      }
    },

    remove(id) {
      const idx = this.items.findIndex(t => t.id === id);
      if (idx !== -1) {
        this.items.splice(idx, 1);
      }
    },

    clear() {
      this.items = [];
    }
  });

  // 2. Global showToast Bridge
  window.showToast = function (message, type = 'info', timeout = 5000) {
    if (window.Alpine && Alpine.store('toasts')) {
      Alpine.store('toasts').add(message, type, timeout);
    } else {
      console.log(`[Toast ${type}] ${message}`);
    }
  };

  // 3. Process any server-rendered legacy flash messages into Alpine toasts
  function processLegacyFlashes() {
    const container = document.getElementById('legacy-flash-messages');
    if (!container) return;

    const flashes = container.querySelectorAll('.flash-data');
    flashes.forEach((flash) => {
      const message = flash.getAttribute('data-message');
      const category = flash.getAttribute('data-category') || 'info';
      window.showToast(message, category);
    });

    container.innerHTML = '';
  }

  processLegacyFlashes();
});

(function () {
  /**
   * HTMX SECURITY & EVENT HOOKS
   */
  function setupHtmx() {
    if (!window.htmx) return;

    // 1. CSRF Token Injection
    document.addEventListener('htmx:configRequest', (evt) => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      if (csrfToken) {
        evt.detail.headers['X-CSRFToken'] = csrfToken;
      }
    });

    // 2. Response Error Handling
    document.addEventListener('htmx:responseError', (evt) => {
      if (evt.detail.path === '/api/ui/pulse' || evt.detail.target?.id === 'aria-ui-pulse') {
        return; // Silent failure on background polling
      }
      const errorMsg = evt.detail.xhr?.responseText || 'An unexpected error occurred.';
      if (window.showToast) {
        window.showToast(errorMsg, 'error');
      }
    });
  }

  /**
   * ROOM DISCOVERY & CALENDAR SYNC
   */
  window.selectRoom = function (roomId, type) {
    // Highlight room cards
    document.querySelectorAll('.aria-room-card').forEach(c => c.classList.remove('active', 'ring-2', 'ring-blue-600'));
    const activeCard = document.querySelector(`.aria-room-card[data-room-id="${roomId}"]`);
    if (activeCard) {
      activeCard.classList.add('active', 'ring-2', 'ring-blue-600');
    }

    // Sync with legacy selectors for FullCalendar compatibility
    const selectorId = (type === 'r') ? '#nroomSelector' : '#eroomSelector';
    const selector = document.querySelector(selectorId);
    if (selector) {
      selector.value = roomId;
      selector.dispatchEvent(new Event('change'));
    }

    // Pre-fill booking modals
    document.querySelectorAll('select[name="roomSelect"]').forEach(select => {
      select.value = roomId;
    });

    console.log(`[ARIA Discovery] Selected room ${roomId} (type: ${type})`);
  };

  /**
   * ANNOUNCEMENT ACTIONS
   */
  window.deleteAnnouncement = function (announceId) {
    if (!announceId || !window.htmx) return;
    const target = document.getElementById('announcement-list');
    if (target) {
      htmx.ajax('POST', '/delete-announcement', {
        target: '#announcement-list',
        swap: 'innerHTML',
        values: { AnnounceId: announceId },
      });
    }
  };

  function init() {
    document.body.classList.add('aria-ui-modern');
    setupHtmx();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
