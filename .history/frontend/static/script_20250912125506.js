// Frontend-only script: proxies requests to backendBaseUrl from config
(function () {
  const originalFetch = window.fetch;
  function withBase(path) {
    const base = (window.APP_CONFIG && window.APP_CONFIG.backendBaseUrl) || "";
    if (!base) return path;
    if (path.startsWith("http://") || path.startsWith("https://")) return path;
    return base.replace(/\/+$/, "") + "/" + path.replace(/^\/+/, "");
  }

  // Wrap global functions expected by index.html
  window.capture = async function () {
    // Reuse the app's existing script by loading it and letting it run,
    // but we intercept fetch below to prefix backend URL.
  };

  // Load the original app script to keep behavior
  const s = document.createElement("script");
  s.src = "/static/script.js";
  s.onload = function () {
    // Monkey-patch fetch after original script is present
    window.fetch = function (input, init) {
      if (typeof input === "string") {
        input = withBase(input);
      } else if (input && input.url) {
        input = withBase(input.url);
      }
      return originalFetch(input, init);
    };
  };
  document.head.appendChild(s);
})();
