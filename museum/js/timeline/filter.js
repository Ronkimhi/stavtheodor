// The filter dropdown: periods list + artist type-ahead, with fly-to and dimming.

import { periodColor } from './layout.js';

export function initFilter({ index, laid, viewport, stage, openArtist }) {
  const btn = document.getElementById('filter-btn');
  const panel = document.getElementById('filter-panel');
  let open = false;
  let activePeriod = null;

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function render(query = '') {
    const q = query.trim().toLowerCase();
    const artists = q
      ? index.artists.filter((a) => a.name.toLowerCase().includes(q))
      : [];
    let i = 0;
    const d = () => `animation-delay:${Math.min(i++ * 30, 360)}ms`;
    panel.innerHTML = `
      <input class="fp-search" type="search" placeholder="Search an artist…"
             value="${esc(query)}" aria-label="Search artists">
      ${q ? `
        <div class="fp-heading" style="${d()}">Artists</div>
        ${artists.map((a) => `
          <button class="fp-item" style="${d()}" data-artist="${esc(a.slug)}">
            <span>${esc(a.name)}</span><span class="fp-sub">${a.born ?? ''}–${a.died ?? ''}</span>
          </button>`).join('') || `<div class="fp-item" style="${d()}"><em>No one by that name here.</em></div>`}
      ` : `
        <div class="fp-heading" style="${d()}">Periods</div>
        ${index.periods.map((p) => `
          <button class="fp-item ${p.id === activePeriod ? 'active' : ''}" style="${d()}" data-period="${esc(p.id)}">
            <span><i class="fp-swatch" style="background:${periodColor(p.id)}"></i>${esc(p.name)}</span>
            <span class="fp-sub">${p.start}–${p.end}</span>
          </button>`).join('')}
      `}
      ${activePeriod ? `<button class="fp-clear" style="${d()}">Show every period</button>` : ''}
    `;

    const search = panel.querySelector('.fp-search');
    search.addEventListener('input', () => {
      const v = search.value;
      const pos = search.selectionStart;
      render(v);
      const s2 = panel.querySelector('.fp-search');
      s2.focus();
      s2.setSelectionRange(pos, pos);
    });
    panel.querySelectorAll('[data-period]').forEach((el) =>
      el.addEventListener('click', () => {
        selectPeriod(el.dataset.period === activePeriod ? null : el.dataset.period);
        toggle(false);
      }));
    panel.querySelectorAll('[data-artist]').forEach((el) =>
      el.addEventListener('click', () => {
        toggle(false);
        goToArtist(el.dataset.artist);
      }));
    panel.querySelector('.fp-clear')?.addEventListener('click', () => {
      selectPeriod(null);
      toggle(false);
    });
  }

  function selectPeriod(id, fly = true) {
    activePeriod = id;
    stage.classList.toggle('filtered', !!id);
    document.querySelectorAll('.band').forEach((b) =>
      b.classList.toggle('focus', b.dataset.period === id));
    document.querySelectorAll('.artist-node').forEach((n) => {
      const a = laid.artists.find((x) => x.slug === n.dataset.slug);
      n.classList.toggle('focus', !!id && !!a && a.periods.includes(id));
    });
    if (id) {
      history.replaceState(null, '', '#' + id);
      if (fly) {
        const p = laid.periods.find((x) => x.id === id);
        viewport.flyToRect(p.x, p.y, p.w, p.h);
      }
    } else {
      history.replaceState(null, '', location.pathname);
    }
  }

  function goToArtist(slug, fly = true) {
    const a = laid.artists.find((x) => x.slug === slug);
    if (!a) return;
    history.replaceState(null, '', '#artist=' + slug);
    if (fly) viewport.flyTo({ x: a.x, y: a.y }, Math.max(viewport.cam.s, 2.1));
    setTimeout(() => openArtist(a), fly ? 500 : 0);
  }

  function toggle(to = !open) {
    open = to;
    btn.setAttribute('aria-expanded', String(open));
    if (open) {
      panel.hidden = false;
      panel.classList.add('opening');
      render();
      setTimeout(() => panel.querySelector('.fp-search')?.focus({ preventScroll: true }), 80);
    } else {
      panel.classList.remove('opening');
      panel.hidden = true;
    }
  }

  btn.addEventListener('click', () => toggle());
  document.addEventListener('pointerdown', (e) => {
    if (open && !panel.contains(e.target) && e.target !== btn) toggle(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && open) toggle(false);
  });

  // Deep links: #period-id or #artist=slug
  function applyHash(fly) {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h) return;
    if (h.startsWith('artist=')) goToArtist(h.slice(7), fly);
    else if (index.periods.some((p) => p.id === h)) selectPeriod(h, fly);
  }
  applyHash(true);

  return { selectPeriod, goToArtist };
}
