// Data loaders + Wikimedia image URL fallbacks.

let _index = null;
const _artists = new Map();

export async function loadIndex() {
  if (_index) return _index;
  const r = await fetch('/museum/data/index.json');
  if (!r.ok) throw new Error('index.json ' + r.status);
  _index = await r.json();
  return _index;
}

export async function loadArtist(slug) {
  if (_artists.has(slug)) return _artists.get(slug);
  const r = await fetch(`/museum/data/artists/${slug}.json`);
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

export function lifeDates(a) {
  if (!a.born) return '';
  return a.died ? `${a.born}–${a.died}` : `b. ${a.born}`;
}

// Wikidata descriptions often embed life dates ("French painter (1840–1926)")
// which we already display separately.
export function oneLinerOf(a) {
  return (a.oneLiner || '').replace(/\s*\(\d{4}[^)]*\)/, '');
}
