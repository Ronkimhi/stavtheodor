// Click-to-inspect: zoomed hi-res view + placard panel with story and fun facts.

import { filePathUrl } from '../shared/data.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function createInspector(artist, { onOpen, onClose } = {}) {
  const root = document.getElementById('inspect-root');
  let current = -1;
  let el = null;

  function dims(p) {
    const parts = [];
    if (p.year) parts.push(String(p.year));
    if (p.cm) parts.push(`${p.cm.h} × ${p.cm.w} cm`);
    return parts;
  }

  function open(index) {
    close(true);
    current = index;
    const p = artist.paintings[index];
    onOpen?.(index);

    el = document.createElement('div');
    el.className = 'inspect';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', p.title);
    el.innerHTML = `
      <div class="inspect-stage" id="ins-stage">
        <span class="inspect-zoomhint">scroll to zoom · drag to pan</span>
        <img class="inspect-img" id="ins-img" alt="${esc(p.title)}" draggable="false">
        <button class="inspect-close" aria-label="Close">×</button>
        <div class="inspect-nav">
          <button id="ins-prev">← Prev</button>
          <button id="ins-next">Next →</button>
        </div>
      </div>
      <aside class="inspect-panel">
        <h2 class="inspect-title">${esc(p.title)}</h2>
        <div class="inspect-meta">
          ${dims(p).map((d) => `<span>${esc(d)}</span>`).join('')}
          ${p.collection ? `<span>${esc(p.collection)}</span>` : ''}
        </div>
        ${p.story?.extract ? `<p class="inspect-story">${esc(p.story.extract)}</p>` : ''}
        ${p.facts?.length ? `
          <div class="inspect-facts">
            <h3>From Wikipedia</h3>
            ${p.facts.map((f) => `
              <p class="inspect-fact">${esc(f.text)}
                <a href="${esc(f.source)}" target="_blank" rel="noopener">${esc(f.section)} →</a>
              </p>`).join('')}
          </div>` : ''}
        <p class="inspect-attr">
          ${p.license?.credit && !/^unknown/i.test(p.license.credit) ? esc(p.license.credit) + ' · ' : ''}
          ${p.license?.name ? esc(p.license.name) + ' · ' : ''}
          ${p.story?.source ? `Text: <a href="${esc(p.story.source)}" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) · ` : ''}
          Image: <a href="https://commons.wikimedia.org/wiki/${esc(encodeURIComponent(p.image.file))}" target="_blank" rel="noopener">Wikimedia Commons</a>
        </p>
      </aside>
    `;
    root.appendChild(el);
    requestAnimationFrame(() => el.classList.add('open'));

    const img = el.querySelector('#ins-img');
    img.src = p.image.thumb1600 || p.image.thumb640;
    img.onerror = () => {
      img.onerror = null;
      img.src = filePathUrl(p.image.file, 1600);
    };
    img.onload = () => fit(img);
    if (img.complete && img.naturalWidth) fit(img);

    el.querySelector('.inspect-close').addEventListener('click', () => close());
    el.querySelector('#ins-prev').addEventListener('click', () =>
      open((index - 1 + artist.paintings.length) % artist.paintings.length));
    el.querySelector('#ins-next').addEventListener('click', () =>
      open((index + 1) % artist.paintings.length));

    initPanZoom(el.querySelector('#ins-stage'), img);
    document.addEventListener('keydown', keys);
  }

  function keys(e) {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') el?.querySelector('#ins-prev')?.click();
    else if (e.key === 'ArrowRight') el?.querySelector('#ins-next')?.click();
  }

  function close(silent = false) {
    document.removeEventListener('keydown', keys);
    if (el) {
      const done = el;
      done.classList.remove('open');
      setTimeout(() => done.remove(), 360);
      el = null;
    }
    if (current !== -1 && !silent) {
      current = -1;
      onClose?.();
    }
  }

  return { open, close, isOpen: () => !!el };
}

// wheel/drag/pinch pan-zoom for the inspect image
function fit(img) {
  const stage = img.parentElement;
  const sw = stage.clientWidth, sh = stage.clientHeight;
  const s = Math.min((sw * 0.86) / img.naturalWidth, (sh * 0.86) / img.naturalHeight);
  img._z = { s, min: s * 0.8, max: Math.max(s * 6, 2), x: (sw - img.naturalWidth * s) / 2, y: (sh - img.naturalHeight * s) / 2 };
  apply(img);
}

function apply(img) {
  const z = img._z;
  img.style.transform = `translate(${z.x}px, ${z.y}px) scale(${z.s})`;
}

function initPanZoom(stage, img) {
  const pointers = new Map();
  let pinch = null;

  stage.addEventListener('wheel', (e) => {
    if (!img._z) return;
    e.preventDefault();
    const z = img._z;
    const k = Math.exp(-e.deltaY * (e.ctrlKey ? 0.012 : 0.0016));
    zoomAt(e.clientX, e.clientY, k);
  }, { passive: false });

  function zoomAt(cx, cy, k) {
    const z = img._z;
    const r = stage.getBoundingClientRect();
    const px = cx - r.left, py = cy - r.top;
    const ns = Math.max(z.min, Math.min(z.max, z.s * k));
    const real = ns / z.s;
    z.x = px - (px - z.x) * real;
    z.y = py - (py - z.y) * real;
    z.s = ns;
    apply(img);
  }

  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('button')) return;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      pinch = { d: Math.hypot(a.x - b.x, a.y - b.y) };
    }
    try { stage.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ }
    stage.classList.add('dragging');
  });
  stage.addEventListener('pointermove', (e) => {
    const p = pointers.get(e.pointerId);
    if (!p || !img._z) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    p.x = e.clientX; p.y = e.clientY;
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, d / pinch.d);
      pinch.d = d;
    } else {
      img._z.x += dx;
      img._z.y += dy;
      apply(img);
    }
  });
  const up = (e) => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch = null;
    if (!pointers.size) stage.classList.remove('dragging');
  };
  stage.addEventListener('pointerup', up);
  stage.addEventListener('pointercancel', up);
}
