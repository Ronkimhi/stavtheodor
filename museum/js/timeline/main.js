// Timeline boot: build the world DOM, wire viewport + filter + placard.

import { loadIndex, fmtYear, fmtRange, lifeDates } from '../shared/data.js';
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

  // Rounder years survive when labels collide on screen (see updateAxisLabels).
  const tickPriority = (year) => {
    const a = Math.abs(year);
    for (const [step, pr] of [[20000, 8], [10000, 7], [5000, 6], [2000, 5],
      [1000, 4], [500, 3], [250, 2], [100, 1]]) {
      if (a % step === 0) return pr;
    }
    return 0;
  };

  const axisLabels = [];
  for (const t of laid.ticks) {
    const tick = document.createElement('div');
    tick.className = 'axis-tick';
    tick.style.left = t.x + 'px';
    const lab = document.createElement('div');
    lab.className = 'axis-label';
    lab.style.left = t.x + 'px';
    lab.style.top = '86px';
    lab.textContent = fmtYear(t.year);
    frag.append(tick, lab);
    axisLabels.push({ el: lab, x: t.x, w: 90, pr: tickPriority(t.year) });
  }

  // Year labels keep a constant screen size while their world positions
  // compress with zoom, so at low zoom (and across time-scale segment
  // boundaries) they physically overlap. Cull per scale change: walk the
  // ticks by priority and hide any label whose screen box would collide
  // with one already kept.
  const labelOrder = [...axisLabels].sort((p, q) => q.pr - p.pr || p.x - q.x);
  let labelS = 0;
  const updateAxisLabels = (s, force = false) => {
    if (!force && Math.abs(s / labelS - 1) < 0.04) return;
    labelS = s;
    const scale = s / Math.max(s, 0.55); // on-screen label scale, mirrors --inv
    const GAP = 16;
    const kept = [];
    for (const L of labelOrder) {
      const half = (L.w * scale + GAP) / 2;
      const c = L.x * s;
      const clash = kept.some((k) => c - half < k.hi && c + half > k.lo);
      L.el.classList.toggle('culled', clash);
      if (!clash) kept.push({ lo: c - half, hi: c + half });
    }
  };

  laid.periods.forEach((p) => {
    const band = document.createElement('div');
    band.className = 'band';
    band.dataset.period = p.id;
    band.style.cssText = `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px`;
    band.style.setProperty('--pc', periodColor(p.id));
    const label = document.createElement('div');
    label.className = 'band-label';
    label.innerHTML = `<span class="band-name"></span><small>${fmtRange(p.start, p.end)}</small>`;
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
    node.setAttribute('aria-label', lifeDates(a) ? `${a.name}, ${lifeDates(a)}` : a.name);
    node.innerHTML = `
      <span class="artist-dot"></span>
      ${a.portrait ? `<img class="artist-portrait" loading="lazy" src="${a.portrait}" alt="">` : ''}
      <span>
        <span class="artist-name"><span class="an-full"></span><span class="an-short"></span></span>
        <span class="artist-years">${lifeDates(a)}</span>
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

  // Fade the page heading the moment any of the map slides under it, not
  // just at the deepest zoom tier. Hysteresis keeps it from flickering at
  // the boundary; the CSS opacity transition does the rest.
  const canvasHead = document.querySelector('.canvas-head');
  let headBottom = 0, headAway = false;
  const measureHead = () => { headBottom = canvasHead.getBoundingClientRect().bottom; };
  measureHead();
  addEventListener('resize', measureHead);
  document.fonts?.ready.then(measureHead);

  const viewport = new Viewport(stage, world, laid.world, {
    onZoomTier: (tier) => {
      stage.classList.remove('tier-0', 'tier-1', 'tier-2');
      stage.classList.add('tier-' + tier);
    },
    onChange: (cam) => {
      const worldTop = -cam.y * cam.s; // screen y of the map's top edge
      const away = worldTop < headBottom + (headAway ? 28 : 8);
      if (away !== headAway) {
        headAway = away;
        stage.classList.toggle('head-away', away);
      }
      updateAxisLabels(cam.s);
    },
  });
  viewport.fitAll();

  // real label widths (fonts may swap in late; re-measure then)
  const measureAxis = () => {
    for (const L of axisLabels) L.w = L.el.offsetWidth || L.w;
    updateAxisLabels(viewport.cam.s, true);
  };
  measureAxis();
  document.fonts?.ready.then(measureAxis);

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
