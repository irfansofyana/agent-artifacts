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

(() => {
  const list = document.querySelector('#artifact-list');
  const input = document.querySelector('#artifact-search');
  const sort = document.querySelector('#artifact-sort');
  if (!list || !input || !sort) return;
  const rows = [...list.querySelectorAll('[data-artifact-row]')];
  const summary = document.querySelector('#result-summary');
  const clear = document.querySelector('#clear-search');
  const empty = document.querySelector('#empty-state');
  const render = () => {
    const query = input.value.trim().toLocaleLowerCase();
    const matches = rows.filter(row => [row.querySelector('h3')?.textContent, row.querySelector('p')?.textContent, row.dataset.slug, row.dataset.type, row.dataset.date].join(' ').toLocaleLowerCase().includes(query));
    matches.sort((a,b) => sort.value === 'title'
      ? a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent,'en')
      : sort.value === 'oldest' ? a.dataset.date.localeCompare(b.dataset.date) : b.dataset.date.localeCompare(a.dataset.date));
    list.replaceChildren(...matches);
    summary.textContent = query ? `${matches.length} result${matches.length === 1 ? '' : 's'} for “${input.value.trim()}”` : `${matches.length} artifacts`;
    empty.hidden = matches.length !== 0;
    clear.hidden = !query;
  };
  input.addEventListener('input',render);
  sort.addEventListener('change',render);
  clear.addEventListener('click',() => { input.value='';render();input.focus(); });
  document.addEventListener('keydown',event => {
    if (event.key === '/' && !['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)) { event.preventDefault();input.focus(); }
    if (event.key === 'Escape' && document.activeElement === input && input.value) { input.value='';render(); }
  });
})();
