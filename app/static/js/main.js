/* DevFlow dashboard – theme handling plus live status from the JSON API. */
(function () {
  "use strict";

  var THEME_KEY = "devflow-theme";
  var root = document.documentElement;

  function storedTheme() {
    try {
      return window.localStorage.getItem(THEME_KEY);
    } catch (error) {
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
      /* storage can be disabled; the theme still applies for this page view */
    }
  }

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var button = document.getElementById("theme-toggle");
    if (!button) return;
    var isDark = theme === "dark";
    button.setAttribute("aria-pressed", String(isDark));
    button.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
    var label = button.querySelector(".theme-label");
    if (label) label.textContent = isDark ? "theme: dark" : "theme: light";
  }

  function initialTheme() {
    var saved = storedTheme();
    if (saved === "light" || saved === "dark") return saved;
    var prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    return prefersLight ? "light" : "dark";
  }

  applyTheme(initialTheme());

  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      storeTheme(next);
    });
  }

  function setBadge(state, text) {
    var badge = document.getElementById("health-badge");
    if (!badge) return;
    badge.dataset.state = state;
    badge.textContent = text;
  }

  function checkHealth() {
    setBadge("pending", "checking…");
    return fetch("/health", { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        setBadge(data.status === "healthy" ? "healthy" : "error", data.status || "unknown");
      })
      .catch(function () {
        setBadge("error", "unreachable");
      });
  }

  function fillBuildInfo() {
    return fetch("/api/info", { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        var build = data.build || {};
        var pairs = [
          ["app-version", "v" + data.version],
          ["commit-sha", build.commit || "not available"],
          ["build-commit", build.commit || "—"],
          ["build-number", build.build_number || "—"],
          ["build-branch", build.branch || "—"],
          ["build-time", build.collected_at || "—"],
        ];
        pairs.forEach(function (pair) {
          var element = document.getElementById(pair[0]);
          if (element) element.textContent = pair[1];
        });
      })
      .catch(function () {
        /* the server-rendered values stay in place when the API is unreachable */
      });
  }

  var refresh = document.getElementById("refresh-status");
  if (refresh) {
    refresh.addEventListener("click", function () {
      checkHealth();
      fillBuildInfo();
    });
  }

  checkHealth();
  fillBuildInfo();
})();
