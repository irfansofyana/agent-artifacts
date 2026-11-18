// Toggles the "swipe sideways" hint only for tables that actually overflow.
(function () {
  function sync() {
    document.querySelectorAll('.table-wrap').forEach(function (wrap) {
      var hint = wrap.previousElementSibling;
      if (!hint || !hint.classList.contains('table-hint')) return;
      hint.hidden = wrap.scrollWidth <= wrap.clientWidth + 1;
    });
  }
  sync();
  window.addEventListener('resize', sync);
  window.addEventListener('orientationchange', sync);
})();
