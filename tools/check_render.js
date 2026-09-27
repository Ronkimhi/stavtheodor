#!/usr/bin/env node
/* The rendered-language check, in a real browser (Chromium via the global Playwright install).

   What it proves, page by page, in a fresh browser context with empty storage:
     - the page opens in English: at least 90% of the words in document.body.innerText are Latin
       and document.documentElement.lang is "en" (site owner's decision, 2026-09-26)
     - the same holds with JavaScript disabled, so the English default is in the markup itself
       (what a crawler that does not run scripts, or a reader with scripts blocked, gets)
   and once, on one inner page:
     - the switch works: clicking עברית shows Hebrew, and a reload keeps it (localStorage radarLang).
   and on the homepage and every buyer variant, on a 360 by 780 screen, in English and in Hebrew:
     - both opening lines (#l1, #l2) end inside the screen: the right edge of the visible language's
       span is at most 360 px (2026-09-27; a restaurants line reached 398 px). The lines are measured
       after the opening splits their letters, as a phone shows them; without WebGL they are laid out
       for the measurement. Layout, not visibility: the letters may still be at opacity 0.
   and on every buyer variant that brings its own rooms to the opening ("rooms" in its JSON), on a
   1280 by 900 screen and on a 360 by 780 phone (where each room is drawn whole):
     - the page requests the before and the after image of each of its rooms and each answers 200,
       it never requests the homepage's images for a slot the variant replaced, and it logs no
       console error (the blocked analytics requests aside); the entrance plays to its end. Without
       WebGL only the first room is fetched (it is preloaded), so only that pair is required.

   Local (default): serves this repo on a loopback port and checks every URL in sitemap.xml
   outside /museum/, then the buyer variants of the homepage (content/variants/*.json: noindex
   and in no sitemap, so they are read from their JSON; checked in both modes). Against
   production, the key pages only:

       node tools/check_render.js
       node tools/check_render.js --base https://stavtheodor.com
       node tools/check_render.js --base https://stavtheodor.com --all

   Needs: node, and playwright installed globally (npm i -g playwright; npx playwright install chromium).
   Exit 1 on any failure. */
'use strict';
const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const SITE = 'https://stavtheodor.com';
const MIN_LATIN = 0.9;
const KEY_PAGES = ['/', '/advisory/', '/projects/', '/radar/', '/art-curator-new-jersey/', '/art-curator-new-york/'];
const NARROW = { width: 360, height: 780 };  /* the smallest common phone: the opening lines must fit it */
const ANALYTICS = /googletagmanager|google-analytics|gstatic|googleapis/;  /* blocked in every context */

function loadPlaywright() {
  try { return require('playwright'); } catch (e) { /* not on the local path */ }
  const globalRoot = execSync('npm root -g', { encoding: 'utf8' }).trim();
  return require(path.join(globalRoot, 'playwright'));
}

function args() {
  const a = process.argv.slice(2);
  const out = { base: null, all: false };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--base') { out.base = a[++i]; }
    else if (a[i] === '--all') { out.all = true; }
    else if (a[i] === '--help' || a[i] === '-h') { console.log(fs.readFileSync(__filename, 'utf8').split('*/')[0]); process.exit(0); }
    else { console.error('unknown argument ' + a[i]); process.exit(2); }
  }
  return out;
}

function sitemapPaths() {
  /* sitemap.xml is an index over child sitemaps (tools/build_sitemap.py); a flat urlset still works */
  const read = f => fs.readFileSync(path.join(ROOT, f), 'utf8');
  const locs = xml => [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
  const index = read('sitemap.xml');
  let urls = [];
  if (index.includes('<sitemapindex')) {
    for (const child of locs(index)) { urls = urls.concat(locs(read(child.replace(SITE + '/', '')))); }
  } else {
    urls = locs(index);
  }
  return urls.map(u => u.replace(SITE, '')).filter(p => !p.startsWith('/museum'));
}

function variantPaths() {
  /* the buyer variants of the homepage, /<path>/ from content/variants/<id>.json (none is fine) */
  const dir = path.join(ROOT, 'content', 'variants');
  if (!fs.existsSync(dir)) { return []; }
  return fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort()
    .map(f => '/' + JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')).path.replace(/^\/+|\/+$/g, '') + '/');
}

function variantRooms() {
  /* the buyer variants that bring their own rooms to the opening: [{ path, rooms }] */
  const dir = path.join(ROOT, 'content', 'variants');
  if (!fs.existsSync(dir)) { return []; }
  return fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort()
    .map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')))
    .filter(v => Array.isArray(v.rooms) && v.rooms.length)
    .map(v => ({ path: '/' + v.path.replace(/^\/+|\/+$/g, '') + '/', rooms: v.rooms }));
}

function homeRooms() {
  /* the homepage's rooms in slot order, [before, after] under /images/home2/, from PAIRS in js/home-opening.js */
  const js = fs.readFileSync(path.join(ROOT, 'js', 'home-opening.js'), 'utf8');
  return [...js.matchAll(/cap: '\w+',[^\n]*?land: \{ b: '([^']+)', a: '([^']+)'/g)].map(m => [m[1], m[2]]);
}

const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'application/javascript', '.json': 'application/json',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.mp4': 'video/mp4',
  '.xml': 'application/xml', '.txt': 'text/plain; charset=utf-8', '.md': 'text/markdown; charset=utf-8', '.ico': 'image/x-icon' };

function serve() {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      if (p.endsWith('/')) { p += 'index.html'; }
      const file = path.join(ROOT, p);
      if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
        res.writeHead(404); res.end('not found'); return;
      }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    });
    server.listen(0, '127.0.0.1', () => resolve({ server, base: 'http://127.0.0.1:' + server.address().port }));
  });
}

const LATIN = /[A-Za-z][A-Za-z'’\-]*/g;
const HEBREW = /[֐-׿][֐-׿'"׳״\-]*/g;
const wordsOf = text => ({ latin: (text.match(LATIN) || []).length, hebrew: (text.match(HEBREW) || []).length });

/* innerText is read only once the theme stylesheet is applied: before that, nothing is hidden yet */
async function settled(page) {
  await page.waitForFunction(() => Array.from(document.styleSheets).some(s => s.href && s.href.indexOf('/css/theme.css') >= 0), null, { timeout: 15000 });
}

async function readPage(page) {
  await settled(page);
  return page.evaluate(() => ({
    lang: document.documentElement.lang,
    bodyEn: document.body.classList.contains('lang-en'),
    bodyHe: document.body.classList.contains('lang-he'),
    text: document.body.innerText || '',
    title: document.title,
  }));
}

/* The two opening lines on a narrow phone, in both languages, on each homepage-shaped page: the right edge
   of the visible language's span in #l1 and #l2 must stay inside the screen. Measured after the opening
   has split the letters (what a phone with WebGL shows) or once it has fallen back to the static figures,
   in which case the lines are laid out (body.gl) for the measurement only. Layout, not visibility. */
async function heroWidths(browser, base, paths, quiet) {
  const fails = [];
  let widest = null;
  for (const p of paths) {
    for (const lang of ['en', 'he']) {
      const context = await browser.newContext({ viewport: NARROW });
      await context.route(ANALYTICS, quiet);
      if (lang === 'he') { await context.addInitScript(() => { try { localStorage.setItem('radarLang', 'he'); } catch (e) {} }); }
      const page = await context.newPage();
      const where = `hero width on ${p} (${lang === 'he' ? 'Hebrew' : 'English'}, ${NARROW.width}x${NARROW.height})`;
      try {
        const resp = await page.goto(base + p, { waitUntil: 'load', timeout: 45000 });
        if (!resp || resp.status() !== 200) { fails.push(`${where}: HTTP ${resp ? resp.status() : 'no response'}`); continue; }
        await page.waitForFunction(() => document.querySelector('#l1 .ch, #l2 .ch') || document.body.classList.contains('static'), null, { timeout: 15000 }).catch(() => {});
        const lines = await page.evaluate(async (lang) => {
          const body = document.body;
          const shown = body.classList.contains('gl');
          if (!shown) { body.classList.add('gl'); }  /* the lines are displayed only in the WebGL opening (body.gl .line) */
          const spans = ['l1', 'l2'].map(id => [id, document.querySelector('#' + id + ' [data-l="' + lang + '"]')]);
          for (const [, s] of spans) { if (s) { await document.fonts.load(getComputedStyle(s).font, s.textContent); } }
          await document.fonts.ready;
          const out = spans.map(([id, s]) => {
            if (!s) { return { id, missing: true }; }
            const r = s.getBoundingClientRect();
            return { id, text: s.textContent.trim(), left: r.left, right: r.right, width: r.width };
          });
          if (!shown) { body.classList.remove('gl'); }
          return out;
        }, lang);
        for (const l of lines) {
          if (l.missing) { fails.push(`${where}: #${l.id} has no ${lang} span`); continue; }
          if (!(l.width > 0)) { fails.push(`${where}: #${l.id} is not laid out (width ${l.width})`); continue; }
          if (!widest || l.right > widest.right) { widest = { p, lang, id: l.id, right: l.right }; }
          if (l.right > NARROW.width) {
            fails.push(`${where}: #${l.id} "${l.text}" ends at ${l.right.toFixed(1)}px, past the ${NARROW.width}px screen (${l.width.toFixed(1)}px wide from left ${l.left.toFixed(1)}px)`);
          }
        }
      } catch (e) {
        fails.push(`${where}: ${e.message.split('\n')[0]}`);
      } finally {
        await context.close();
      }
    }
  }
  return { fails, widest };
}

/* A buyer variant with its own rooms, on a desktop screen and on a portrait phone (each room drawn whole): the page
   requests the before and after image of every room it brings (only the preloaded first pair without WebGL) and
   each answers 200, it requests no homepage image of a slot it replaced, it logs no console error outside the
   blocked analytics, and the entrance plays to its end. */
const ROOM_VIEWS = [{ viewport: { width: 1280, height: 900 } }, { viewport: NARROW, isMobile: true, hasTouch: true }];

async function roomLoads(browser, base, quiet) {
  const fails = [];
  let checked = 0;
  const variants = variantRooms(), home = homeRooms(), img = n => '/images/home2/' + n;
  if (variants.length && !home.length) { return { fails: ['js/home-opening.js: no rooms read from PAIRS (did its format change?)'], checked }; }
  for (const v of variants) {
    for (const view of ROOM_VIEWS) {
      const context = await browser.newContext(view);
      await context.route(ANALYTICS, quiet);
      const page = await context.newPage();
      const seen = new Map(), errors = [];
      const rel = u => (u.startsWith(base) ? u.slice(base.length) : u).split('?')[0];
      page.on('response', r => seen.set(rel(r.url()), r.status()));
      page.on('requestfailed', r => { if (!ANALYTICS.test(r.url())) { seen.set(rel(r.url()), (r.failure() || {}).errorText || 'failed'); } });
      page.on('console', m => { if (m.type() === 'error' && !ANALYTICS.test(m.location().url || '')) { errors.push(m.text()); } });
      page.on('pageerror', e => errors.push(e.message));
      const where = `rooms on ${v.path} (${view.viewport.width}x${view.viewport.height})`;
      try {
        const resp = await page.goto(base + v.path, { waitUntil: 'load', timeout: 45000 });
        if (!resp || resp.status() !== 200) { fails.push(`${where}: HTTP ${resp ? resp.status() : 'no response'}`); continue; }
        const mode = await page.waitForFunction(() => { const d = window.__theodoraBrush; return d && d.mode !== 'boot' && d.mode; }, null, { timeout: 15000 })
          .then(h => h.jsonValue()).catch(() => null);
        if (!mode) { fails.push(`${where}: the opening never started (window.__theodoraBrush.mode stayed "boot")`); }
        const want = (mode === 'gl' ? v.rooms : v.rooms.slice(0, 1)).flatMap(r => [img(r.b), img(r.a)]);
        for (let t = 0; t < 60 && !want.every(u => seen.has(u)); t++) { await page.waitForTimeout(250); }
        if (mode === 'gl') {
          await page.waitForFunction(() => window.__theodoraBrush.done, null, { timeout: 20000 })
            .catch(() => fails.push(`${where}: the entrance did not reach its end within 20 s`));
        }
        for (const u of want) { if (seen.get(u) !== 200) { fails.push(`${where}: ${u} ${seen.has(u) ? 'answered ' + seen.get(u) : 'was never requested'}`); } }
        v.rooms.forEach((r, slot) => (home[slot] || []).forEach(n => {
          if (seen.has(img(n))) { fails.push(`${where}: requested the homepage's ${img(n)}, but slot ${slot} is the variant's own room`); }
        }));
        errors.forEach(e => fails.push(`${where}: console error: ${e.split('\n')[0]}`));
        checked++;
      } catch (e) {
        fails.push(`${where}: ${e.message.split('\n')[0]}`);
      } finally {
        await context.close();
      }
    }
  }
  return { fails, checked, pages: variants.length };
}

async function main() {
  const opt = args();
  const { chromium } = loadPlaywright();
  let server = null, base = opt.base;
  let pages;
  if (!base) {
    ({ server, base } = await serve());
    pages = sitemapPaths();
  } else {
    base = base.replace(/\/$/, '');
    const sm = sitemapPaths();
    pages = opt.all ? sm : KEY_PAGES.filter(p => sm.includes(p));  /* the key pages this tree actually publishes */
    if (!opt.all) { const post = sm.find(p => p.startsWith('/radar/') && p !== '/radar/'); if (post) { pages.push(post); } }
  }
  pages = pages.concat(variantPaths());  /* after the sitemap paths, in both modes */
  const browser = await chromium.launch();
  const fails = [];
  let checked = 0;
  const quiet = r => r.abort();
  for (const p of pages) {
    for (const js of [true, false]) {
      const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, javaScriptEnabled: js });
      await context.route(ANALYTICS, quiet);
      const page = await context.newPage();
      const url = base + p;
      const mode = js ? '' : ' (no JS)';
      try {
        const resp = await page.goto(url, { waitUntil: 'load', timeout: 45000 });
        if (!resp || resp.status() !== 200) { fails.push(`${p}${mode}: HTTP ${resp ? resp.status() : 'no response'}`); continue; }
        const r = await readPage(page);
        const w = wordsOf(r.text);
        const share = w.latin / Math.max(1, w.latin + w.hebrew);
        if (r.lang !== 'en') { fails.push(`${p}${mode}: documentElement.lang is "${r.lang}", expected "en"`); }
        if (!r.bodyEn || r.bodyHe) { fails.push(`${p}${mode}: body classes are not lang-en (en=${r.bodyEn}, he=${r.bodyHe})`); }
        if (share < MIN_LATIN) { fails.push(`${p}${mode}: ${Math.round(share * 100)}% Latin words visible (${w.latin} Latin, ${w.hebrew} Hebrew)`); }
        if (js) { checked++; }
      } catch (e) {
        fails.push(`${p}${mode}: ${e.message.split('\n')[0]}`);
      } finally {
        await context.close();
      }
    }
  }

  /* the switch, on one inner page: pick עברית, Hebrew shows, reload, still Hebrew */
  const inner = pages.find(p => p !== '/' && !p.startsWith('/radar/')) || pages.find(p => p !== '/') || '/';
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await context.route(ANALYTICS, quiet);
  const page = await context.newPage();
  try {
    await page.goto(base + inner, { waitUntil: 'load', timeout: 45000 });
    await page.click('.lang-switch button[data-lang="he"]', { timeout: 10000 });
    let r = await readPage(page);
    let w = wordsOf(r.text);
    if (r.lang !== 'he' || !r.bodyHe) { fails.push(`switch on ${inner}: after clicking עברית lang="${r.lang}", body.lang-he=${r.bodyHe}`); }
    if (w.hebrew <= w.latin) { fails.push(`switch on ${inner}: Hebrew not showing after the click (${w.hebrew} Hebrew, ${w.latin} Latin)`); }
    await page.reload({ waitUntil: 'load', timeout: 45000 });
    r = await readPage(page);
    w = wordsOf(r.text);
    if (r.lang !== 'he' || !r.bodyHe || w.hebrew <= w.latin) { fails.push(`switch on ${inner}: the choice did not survive a reload (lang="${r.lang}", ${w.hebrew} Hebrew, ${w.latin} Latin)`); }
  } catch (e) {
    fails.push(`switch on ${inner}: ${e.message.split('\n')[0]}`);
  } finally {
    await context.close();
  }

  /* the opening lines on a narrow phone: the homepage and every buyer variant, English and Hebrew */
  const heroPages = ['/'].concat(variantPaths());
  const hero = await heroWidths(browser, base, heroPages, quiet);
  fails.push(...hero.fails);

  /* the buyer variants' own rooms in the opening */
  const rooms = await roomLoads(browser, base, quiet);
  fails.push(...rooms.fails);

  await browser.close();
  if (server) { server.close(); }
  if (fails.length) {
    console.log(fails.join('\n'));
    console.log(`\ncheck_render: ${fails.length} failure(s) over ${checked} page(s) at ${base}`);
    process.exit(1);
  }
  const w = hero.widest;
  console.log(`check_render: OK, ${checked} page(s) open in English with and without JavaScript (>= ${MIN_LATIN * 100}% Latin, lang="en") at ${base}; the switch shows Hebrew and remembers it (${inner}); `
    + `the opening lines fit a ${NARROW.width}px screen on ${heroPages.length} page(s) in English and Hebrew (widest: ${w ? `${w.right.toFixed(1)}px, #${w.id} on ${w.p} in ${w.lang === 'he' ? 'Hebrew' : 'English'}` : 'none measured'}); `
    + (rooms.pages ? `${rooms.pages} variant(s) load their own opening rooms, desktop and phone, with no console error` : 'no variant brings its own opening rooms'));
}

main().catch(e => { console.error(e); process.exit(1); });
