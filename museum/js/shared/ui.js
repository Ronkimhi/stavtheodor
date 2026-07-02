// The artist placard — a museum wall label, shared by timeline and gallery.

import { loadArtist, artistUrl, lifeDates, oneLinerOf, filePathUrl } from './data.js';

let root = null;
let onCloseCb = null;

const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function ensureRoot() {
  if (!root) root = document.getElementById('placard-root') || document.body;
  return root;
}

let opener = null;

export async function openPlacard(indexArtist, periodsById, { onClose } = {}) {
  closePlacard();
  onCloseCb = onClose || null;
  opener = document.activeElement;
  const holder = ensureRoot();

  const scrim = document.createElement('div');
  scrim.className = 'placard-scrim';
  const card = document.createElement('div');
  card.className = 'placard';
  card.setAttribute('role', 'dialog');
  card.setAttribute('aria-modal', 'true');
  card.setAttribute('aria-label', indexArtist.name);

  const periodNames = (indexArtist.periods || [])
    .map((id) => periodsById?.[id]?.name || id)
    .join(' · ');

  card.innerHTML = `
    <button class="placard-close" aria-label="Close">×</button>
    <div class="placard-head">
      ${indexArtist.portrait
        ? `<img class="placard-portrait" src="${esc(indexArtist.portrait)}" alt="Portrait of ${esc(indexArtist.name)}">`
        : ''}
      <div>
        <div class="placard-name">${esc(indexArtist.name)}</div>
        <div class="placard-dates">${esc([oneLinerOf(indexArtist), lifeDates(indexArtist)].filter(Boolean).join(', '))}</div>
        <div class="placard-periods">${esc(periodNames)}</div>
      </div>
    </div>
    <div class="placard-bio"><em>Loading…</em></div>
  `;

  holder.appendChild(scrim);
  holder.appendChild(card);
  requestAnimationFrame(() => {
    scrim.classList.add('open');
    card.classList.add('open');
  });

  scrim.addEventListener('click', closePlacard);
  card.querySelector('.placard-close').addEventListener('click', closePlacard);
  document.addEventListener('keydown', escClose);
  card.querySelector('.placard-close').focus({ preventScroll: true });

  try {
    const full = await loadArtist(indexArtist.slug);
    if (!card.isConnected) return;
    const bio = card.querySelector('.placard-bio');
    bio.textContent = full.bio?.extract || '';
    const attr = document.createElement('div');
    attr.className = 'placard-attr';
    attr.innerHTML = `Text: <a href="${full.bio?.source || full.wikipedia}" target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0)`;
    bio.after(attr);

    if (full.hasGallery) {
      const cta = document.createElement('a');
      cta.className = 'placard-cta';
      cta.href = artistUrl(full.slug);
      cta.textContent = `Enter Gallery · ${full.paintings.length} works →`;
      attr.after(cta);
    } else {
      const note = document.createElement('span');
      note.className = 'placard-copyright';
      note.innerHTML = `The paintings are still under copyright and cannot be hung here.
        <a href="${full.wikipedia}" target="_blank" rel="noopener">View the work on Wikipedia →</a>`;
      attr.after(note);
    }
  } catch (err) {
    const bio = card.querySelector('.placard-bio');
    if (bio) bio.innerHTML = `Could not load this artist. <a href="javascript:location.reload()">Reload?</a>`;
  }
}

function escClose(e) {
  if (e.key === 'Escape') closePlacard();
}

export function closePlacard() {
  document.removeEventListener('keydown', escClose);
  const holder = ensureRoot();
  holder.querySelectorAll('.placard-scrim, .placard').forEach((el) => {
    el.classList.remove('open');
    setTimeout(() => el.remove(), 350);
  });
  if (opener?.isConnected) opener.focus({ preventScroll: true });
  opener = null;
  if (onCloseCb) { const cb = onCloseCb; onCloseCb = null; cb(); }
}

export { filePathUrl };
