(function () {
  function setupDeleteAnnouncement() {
    window.deleteAnnouncement = function deleteAnnouncement(announceId) {
      if (!announceId) {
        return;
      }

      const target = document.getElementById("announcement-list");
      if (window.htmx && target) {
        htmx.ajax("POST", "/delete-announcement", {
          target: "#announcement-list",
          swap: "innerHTML",
          values: { AnnounceId: announceId },
        });
        return;
      }

      fetch("/delete-announcement", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ AnnounceId: announceId }),
      }).then(function () {
        window.location.reload();
      });
    };
  }

  function installAriaBodyClass() {
    document.body.classList.add("aria-ui");
  }

  document.addEventListener("DOMContentLoaded", function () {
    installAriaBodyClass();
    setupDeleteAnnouncement();
  });
})();
