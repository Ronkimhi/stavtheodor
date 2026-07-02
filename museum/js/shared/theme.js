// Day / night museum. The <head> of each page applies the stored (or system)
// theme before first paint; this module wires the toggle button.

export function initThemeToggle(btn) {
  if (!btn) return;
  const cur = () => document.documentElement.dataset.theme || 'light';
  const paint = () => {
    btn.textContent = cur() === 'dark' ? '☀' : '☾';
    btn.setAttribute('aria-label',
      cur() === 'dark' ? 'Switch to day mode' : 'Switch to night mode');
  };
  btn.addEventListener('click', () => {
    const next = cur() === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('museumTheme', next); } catch (e) { /* private mode */ }
    paint();
  });
  paint();
}
