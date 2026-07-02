// Data loaders + Wikimedia image URL fallbacks.

let _index = null;
const _artists = new Map();

// 'no-cache' = revalidate with the CDN (ETag/304) instead of trusting a
// possibly stale browser copy — data updates show up on the next page load.
export async function loadIndex() {
  if (_index) return _index;
  const r = await fetch('/museum/data/index.json', { cache: 'no-cache' });
  if (!r.ok) throw new Error('index.json ' + r.status);
  _index = await r.json();
  return _index;
}

export async function loadArtist(slug) {
  if (_artists.has(slug)) return _artists.get(slug);
  const r = await fetch(`/museum/data/artists/${slug}.json`, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`artist ${slug} ` + r.status);
  const a = await r.json();
  _artists.set(slug, a);
  return a;
}

// If a stored Commons thumb URL has gone stale (file renamed), this URL
// follows the rename via a redirect on the file title.
export function filePathUrl(fileTitle, width) {
  const name = fileTitle.replace(/^File:/, '');
  return 'https://commons.wikimedia.org/wiki/Special:FilePath/'
    + encodeURIComponent(name) + '?width=' + width;
}

export function artistUrl(slug) {
  return `/museum/gallery/?artist=${encodeURIComponent(slug)}`;
}

// BCE-aware year display: negative years are BCE. "480–430 BCE", "27 BCE–14 CE".
export function fmtYear(y) {
  if (y == null) return '';
  return y < 0 ? `${-y} BCE` : String(y);
}

export function fmtRange(start, end) {
  if (start == null) return '';
  if (end == null || end === start) return fmtYear(start);
  if (start < 0 && end < 0) return `${-start}–${-end} BCE`;
  if (start < 0) return `${-start} BCE–${end} CE`;
  return `${start}–${end}`;
}

export function lifeDates(a) {
  if (!a.born) return '';
  if (!a.died) return a.born < 0 ? `c. ${fmtYear(a.born)}` : `b. ${a.born}`;
  return fmtRange(a.born, a.died);
}

// Wikidata descriptions often embed life dates ("French painter (1840–1926)")
// which we already display separately.
export function oneLinerOf(a) {
  return (a.oneLiner || '').replace(/\s*\((?:born |b\. )?\d{4}[^)]*\)/, '');
}
