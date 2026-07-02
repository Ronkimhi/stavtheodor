// Timeline boot: build the world DOM, wire viewport + filter + placard.

import { loadIndex } from '../shared/data.js';
import { openPlacard } from '../shared/ui.js';
import { initThemeToggle } from '../shared/theme.js';
import { layout, periodColor } from './layout.js';
import { Viewport } from './viewport.js';
import { initFilter } from './filter.js';

const stage = document.getElementById('stage');
const world = document.getElementById('world');

// Compact display name for the mid zoom tier ("Monet", "da Vinci", "van Eyck").
const PARTICLES = new Set(['da', 'de', 'della', 'van', 'von', 'di', 'el', 'le']);
const SHORT_OVERRIDES = { 'Piero della Francesca': 'Piero' };
function shortName(name) {
  if (SHORT_OVERRIDES[name]) return SHORT_OVERRIDES[name];
  const tokens = name
    .replace(/\s+the\s+(Elder|Younger)$/i, '')
    .split(' ');
  if (tokens.length === 1) return name;
  const last = tokens[tokens.length - 1];
  const prev = tokens[tokens.length - 2]?.toLowerCase();
  return PARTICLES.has(prev) && last.length <= 6
    ? tokens.slice(-2).join(' ')
    : last;
}

async function boot() {
  const index = await loadIndex();
  const laid = layout(index);
  const periodsById = Object.fromEntries(index.periods.map((p) => [p.id, p]));

  const frag = document.createDocumentFragment();

  for (const t of laid.ticks) {
    const tick = document.createElement('div');
    tick.className = 'axis-tick';
    tick.style.left = t.x + 'px';
    const lab = document.createElement('div');
    lab.className = 'axis-label';
    lab.style.left = t.x + 'px';
    lab.style.top = '86px';
    lab.textContent = t.year;
    frag.append(tick, lab);
  }

  laid.periods.forEach((p) => {
    const band = document.createElement('div');
    band.className = 'band';
    band.dataset.period = p.id;
    band.style.cssText = `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px`;
    band.style.setProperty('--pc', periodColor(p.id));
    const label = document.createElement('div');
    label.className = 'band-label';
    label.innerHTML = `<span class="band-name"></span><small>${p.start}–${p.end}</small>`;
    label.querySelector('.band-name').textContent = p.name;
    band.appendChild(label);
    if (p.summary) {
      const sum = document.createElement('div');
      sum.className = 'band-summary';
      sum.textContent = p.summary;
      if (p.w < 300) band.classList.add('narrow');
      band.appendChild(sum);
    }
    frag.appendChild(band);
  });

  for (const a of laid.artists) {
    const node = document.createElement('button');
    node.className = 'artist-node';
    node.dataset.slug = a.slug;
    // dot-anchored: the dot sits exactly on the artist's position; text flows
    // away from the nearer band edge so names never spill outside the period.
    if (a.flip) node.classList.add('flip');
    node.style.left = a.x + 'px';
    node.style.top = a.y + 'px';
    node.style.setProperty('--pc', periodColor(a.period.id));
    node.setAttribute('aria-label', `${a.name}, ${a.born ?? ''}–${a.died ?? ''}`);
    node.innerHTML = `
      <span class="artist-dot"></span>
      ${a.portrait ? `<img class="artist-portrait" loading="lazy" src="${a.portrait}" alt="">` : ''}
      <span>
        <span class="artist-name"><span class="an-full"></span><span class="an-short"></span></span>
        <span class="artist-years">${a.born ?? '?'}–${a.died ?? ''}</span>
      </span>`;
    node.querySelector('.an-full').textContent = a.name;
    node.querySelector('.an-short').textContent = shortName(a.name);
    node.addEventListener('click', () => {
      history.replaceState(null, '', '#artist=' + a.slug);
      openArtist(a);
    });
    // keyboard tour: tabbing to an artist flies the camera to them
    node.addEventListener('focus', () => {
      const r = node.getBoundingClientRect();
      const offscreen = r.right < 0 || r.left > innerWidth || r.bottom < 0 || r.top > innerHeight;
      if (viewport.cam.s < 1.6 || offscreen) {
        viewport.flyTo({ x: a.x, y: a.y }, Math.max(viewport.cam.s, 2.1), 450);
      }
    });
    frag.appendChild(node);
  }

  world.appendChild(frag);
  world.style.width = laid.world.w + 'px';
  world.style.height = laid.world.h + 'px';

  const viewport = new Viewport(stage, world, laid.world, {
    onZoomTier: (tier) => {
      stage.classList.remove('tier-0', 'tier-1', 'tier-2');
      stage.classList.add('tier-' + tier);
    },
  });
  viewport.fitAll();

  function openArtist(a) {
    openPlacard(a, periodsById, {
      onClose: () => {
        if (location.hash.startsWith('#artist=')) {
          history.replaceState(null, '', location.pathname);
        }
      },
    });
  }

  const filter = initFilter({ index, laid, viewport, stage, openArtist });

  // keyboard
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      // progressive back: placard → filter panel → active filter → fit all
      // (placard and panel close themselves via their own Escape handlers)
      if (document.querySelector('.placard')) return;
      if (!document.getElementById('filter-panel').hidden) return;
      if (stage.classList.contains('filtered')) return filter.selectPeriod(null);
      return viewport.fitAll();
    }
    if (e.target instanceof Element && e.target.closest('input, .placard')) return;
    const pan = 90 / viewport.cam.s;
    if (e.key === 'ArrowLeft') viewport.cam.x -= pan;
    else if (e.key === 'ArrowRight') viewport.cam.x += pan;
    else if (e.key === 'ArrowUp') viewport.cam.y -= pan;
    else if (e.key === 'ArrowDown') viewport.cam.y += pan;
    else if (e.key === '+' || e.key === '=') return viewport.zoomCenter(1.3);
    else if (e.key === '-') return viewport.zoomCenter(1 / 1.3);
    else if (e.key === '0') return viewport.fitAll();
    else return;
    viewport.clamp();
    viewport.apply();
  });

  initThemeToggle(document.getElementById('theme-btn'));
  document.getElementById('zoom-in').addEventListener('click', () => viewport.zoomCenter(1.45));
  document.getElementById('zoom-out').addEventListener('click', () => viewport.zoomCenter(1 / 1.45));
  document.getElementById('zoom-fit').addEventListener('click', () => viewport.fitAll());

  setTimeout(() => document.getElementById('hint')?.classList.add('faded'), 7000);

  window.__timeline = { index, laid, viewport, filter };
}

boot().catch((err) => {
  console.error(err);
  const msg = document.createElement('p');
  msg.style.cssText = 'position:fixed;top:45%;width:100%;text-align:center;font-style:italic;';
  msg.textContent = 'The museum doors seem stuck — please try reloading.';
  document.body.appendChild(msg);
});
