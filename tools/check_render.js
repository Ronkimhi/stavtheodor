#!/usr/bin/env node
/* The rendered-language check, in a real browser (Chromium via the global Playwright install).

   What it proves, page by page, in a fresh browser context with empty storage:
     - the page opens in English: at least 90% of the words in document.body.innerText are Latin
       and document.documentElement.lang is "en" (site owner's decision, 2026-09-26)
     - the same holds with JavaScript disabled, so the English default is in the markup itself
       (what a crawler that does not run scripts, or a reader with scripts blocked, gets)
   and once, on one inner page:
     - the switch works: clicking עברית shows Hebrew, and a reload keeps it (localStorage radarLang).

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
      await context.route(/googletagmanager|google-analytics|gstatic|googleapis/, quiet);
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
  await context.route(/googletagmanager|google-analytics|gstatic|googleapis/, quiet);
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

  await browser.close();
  if (server) { server.close(); }
  if (fails.length) {
    console.log(fails.join('\n'));
    console.log(`\ncheck_render: ${fails.length} failure(s) over ${checked} page(s) at ${base}`);
    process.exit(1);
  }
  console.log(`check_render: OK, ${checked} page(s) open in English with and without JavaScript (>= ${MIN_LATIN * 100}% Latin, lang="en") at ${base}; the switch shows Hebrew and remembers it (${inner})`);
}

main().catch(e => { console.error(e); process.exit(1); });
