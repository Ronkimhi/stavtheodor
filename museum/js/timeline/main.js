// Timeline boot: build the world DOM, wire viewport + filter + placard.

import { loadIndex } from '../shared/data.js';
import { openPlacard } from '../shared/ui.js';
import { layout } from './layout.js';
import { Viewport } from './viewport.js';
import { initFilter } from './filter.js';

const stage = document.getElementById('stage');
const world = document.getElementById('world');

function tintFor(i, n) {
  // subtle ivory→bronze ramp across periods, never leaving the palette
  const t = i / Math.max(1, n - 1);
  const alpha = 0.05 + 0.13 * t;
  return `rgba(160, 129, 92, ${alpha.toFixed(3)})`;
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

  laid.periods.forEach((p, i) => {
    const band = document.createElement('div');
    band.className = 'band';
    band.dataset.period = p.id;
    band.style.cssText = `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;--band-tint:${tintFor(i, laid.periods.length)}`;
    const label = document.createElement('div');
    label.className = 'band-label';
    label.innerHTML = `${p.name}<small>${p.start}–${p.end}</small>`;
    band.appendChild(label);
    frag.appendChild(band);
  });

  for (const a of laid.artists) {
    const node = document.createElement('button');
    node.className = 'artist-node';
    node.dataset.slug = a.slug;
    node.style.left = a.x + 'px';
    node.style.top = a.y + 'px';
    node.setAttribute('aria-label', `${a.name}, ${a.born ?? ''}–${a.died ?? ''}`);
    node.innerHTML = `
      <span class="artist-dot"></span>
      ${a.portrait ? `<img class="artist-portrait" loading="lazy" src="${a.portrait}" alt="">` : ''}
      <span>
        <span class="artist-name"></span>
        <span class="artist-years">${a.born ?? '?'}–${a.died ?? ''}</span>
      </span>`;
    node.querySelector('.artist-name').textContent = a.name;
    node.addEventListener('click', () => {
      history.replaceState(null, '', '#artist=' + a.slug);
      openArtist(a);
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
    if (e.target.closest('input, .placard')) return;
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
