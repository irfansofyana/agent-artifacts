/* Progressive enhancement only: the page is fully readable without this file. */
(function () {
  "use strict";

  /* Reading progress bar */
  var bar = document.getElementById("progress-bar");
  var ticking = false;
  function updateProgress() {
    ticking = false;
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    var pct = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
    if (bar) bar.style.width = (pct * 100).toFixed(2) + "%";
    updateToc();
  }
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(updateProgress);
  }

  /* Table of contents: mark the section the reader is in.
     Uses one measuring line rather than IntersectionObserver, because the
     headings themselves are only ~36px tall and rarely sit inside an
     observer band, which leaves the list unhighlighted while reading. */
  var tocLinks = Array.prototype.slice.call(
    document.querySelectorAll("#toc a[href^='#']")
  );
  var sections = tocLinks
    .map(function (a) {
      var el = document.getElementById(a.getAttribute("href").slice(1));
      return el ? { link: a, el: el } : null;
    })
    .filter(Boolean);

  function updateToc() {
    if (!sections.length) return;
    var line = Math.min(window.innerHeight * 0.28, 240);
    var current = sections[0];
    sections.forEach(function (s) {
      if (s.el.getBoundingClientRect().top - line <= 0) current = s;
    });
    /* At the very bottom the last heading can never reach the line, so pin it. */
    var doc = document.documentElement;
    if (window.scrollY + window.innerHeight >= doc.scrollHeight - 2) {
      current = sections[sections.length - 1];
    }
    tocLinks.forEach(function (a) {
      if (a === current.link) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  /* rAF is paused while the tab is hidden, so re-sync when it comes back. */
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) updateProgress();
  });
  updateProgress();

  /* Copy buttons */
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var block = btn.closest(".code");
      var code = block && block.querySelector("code");
      if (!code) return;
      var text = code.innerText;
      var done = function (label) {
        var original = "Copy";
        btn.textContent = label;
        window.setTimeout(function () { btn.textContent = original; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () { done("Copied"); },
          function () { done("Press Ctrl+C"); }
        );
      } else {
        var range = document.createRange();
        range.selectNodeContents(code);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        done("Selected");
      }
    });
  });

  /* Table swipe hints: only when the table actually overflows */
  var wraps = Array.prototype.slice.call(document.querySelectorAll(".table-wrap"));
  function updateHints() {
    wraps.forEach(function (wrap) {
      var hint = wrap.querySelector(".table-hint");
      if (hint) hint.hidden = wrap.scrollWidth <= wrap.clientWidth + 1;
    });
  }
  updateHints();
  window.addEventListener("resize", updateHints);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(updateHints);
  if ("ResizeObserver" in window) {
    new ResizeObserver(updateHints).observe(document.body);
  }
})();
