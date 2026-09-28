(() => {
  const root = document.documentElement;
  const button = document.querySelector('[data-theme-toggle]');
  if (!button) return;
  const show = () => {
    const paper = root.dataset.theme === 'paper';
    button.textContent = `Theme: ${paper ? 'Paper' : 'Dark'}`;
    button.setAttribute('aria-label',`Switch to ${paper ? 'dark' : 'paper'} theme`);
    button.setAttribute('aria-pressed',String(paper));
  };
  show();
  button.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'paper' ? 'dark' : 'paper';
    try { localStorage.setItem('artifact-theme',root.dataset.theme); } catch (_) { /* restricted storage: in-page switching still works */ }
    show();
  });
})();
