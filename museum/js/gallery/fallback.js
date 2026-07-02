// Quiet list view: no-WebGL fallback, reduced-motion path, and the screen-reader path.

import { filePathUrl, oneLinerOf, fmtYear } from '../shared/data.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function showListView(artist) {
  const root = document.getElementById('list-root');
  root.innerHTML = `
    <div class="list-view">
      <div class="list-inner">
        <a class="entry-brand" href="/museum/">← THE MUSEUM</a>
        <h1 class="entry-name" style="text-align:left;margin-top:20px;">${esc(artist.name)}</h1>
        <p class="entry-sub" style="text-align:left;">${esc(oneLinerOf(artist))}</p>
        ${artist.paintings.map((p) => `
          <div class="list-item">
            <img loading="lazy" src="${esc(p.image.thumb640)}"
                 data-file="${esc(p.image.file)}" alt="${esc(p.title)}">
            <h2>${esc(p.title)}</h2>
            <div class="inspect-meta">
              ${p.year ? `<span>${fmtYear(p.year)}</span>` : ''}
              ${p.collection ? `<span>${esc(p.collection)}</span>` : ''}
            </div>
            ${p.story?.extract ? `<p>${esc(p.story.extract)}</p>` : ''}
          </div>`).join('')}
        <p class="inspect-attr" style="margin-top:60px;">
          Text: Wikipedia (CC BY-SA 4.0) · Images: Wikimedia Commons ·
          <a href="/museum/gallery/?artist=${esc(artist.slug)}">Try the 3D gallery</a>
        </p>
      </div>
    </div>`;
  root.querySelectorAll('img[data-file]').forEach((img) => {
    img.addEventListener('error', () => {
      img.src = filePathUrl(img.dataset.file, 640);
    }, { once: true });
  });
  document.getElementById('entry')?.remove();
}
