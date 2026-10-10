#!/usr/bin/env python3
"""sitemap.xml for stavtheodor.com: a sitemap index over three child sitemaps (2026-09-26).

  sitemap-pages.xml    the homepage, the hubs (/advisory/, /projects/, /guide/), every advisory, project, partner, guide and
                       local landing page (content/pages/*.json), /contact/ and /about/ (since 2026-09-29), and the
                       buyer pages (content/variants/*.json, indexable since 2026-09-28); each guide URL also lists its
                       proposal photos as image:image entries (2026-10-10)
  sitemap-radar.xml    the Art Radar archive and every post (content/posts.html)
  sitemap-museum.xml   the Museum's static pages (museum/index.html, museum/artists/, one
                       page per artist), which used to dilute one flat sitemap

lastmod moves only when the page a reader gets actually changes (since 2026-10-01). Each page and museum URL is
dated by a fingerprint of its built index.html, stored with its date in tools/sitemap-lastmod.json (committed with
the build output): same fingerprint, same lastmod; a new fingerprint dates the URL now. The fingerprint is the
page's content only: its text in both languages, the href, src, alt, content and title values, and its JSON-LD,
with the shared nav, footer and Write to Stav pop-up (its <dialog>), every other script, every style block, HTML comments and ?v= cache busters left
out, so a change to the site chrome, a code comment or a stylesheet version moves no lastmod. A URL missing from
the file (a lost file, a merge conflict resolved by deleting its lines) is dated by the newest commit that changed
its fingerprint, so the file can always be rebuilt from git. A post keeps its own dateModified and the /radar/
archive the newest of them. Run by python3 build.py after the pages are written; run it alone from the repo root
after editing content. Rebuilding an unchanged tree changes nothing.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import site_chrome as sc  # noqa: E402
from site_chrome import SITE  # noqa: E402

os.chdir(ROOT)
STORE = 'tools/sitemap-lastmod.json'

COMMENT = re.compile(r'<!--.*?-->', re.S)
SCRIPT = re.compile(r'<script\b([^>]*)>(.*?)</script>', re.S | re.I)
STYLE = re.compile(r'<style\b.*?</style>', re.S | re.I)
CHROME = re.compile(r'<(nav|footer|dialog)\b.*?</\1>', re.S | re.I)  # dialog: the Write to Stav pop-up (2026-10-06)
TAG = re.compile(r'<[^>]*>')
ATTR = re.compile(r'\b(href|src|alt|content|title)\s*=\s*"([^"]*)"', re.I)
BUSTER = re.compile(r'\?v=[\w.-]+')


def fingerprint(html):
    """A short hash of what a reader and a crawler get from the page, without the chrome and the build noise."""
    html = COMMENT.sub(' ', html)
    html = SCRIPT.sub(lambda m: ' ' + m.group(2) + ' ' if 'ld+json' in m.group(1) else ' ', html)
    html = STYLE.sub(' ', html)
    html = CHROME.sub(' ', html)
    html = TAG.sub(lambda m: ' ' + ' '.join(v for _, v in ATTR.findall(m.group(0))) + ' ', html)
    text = ' '.join(BUSTER.sub('', html).split())
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def now():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_store():
    try:
        return json.load(open(STORE, encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_store(store):
    lines = [f'  {json.dumps(k)}: {json.dumps(store[k], sort_keys=True)}' for k in sorted(store)]
    open(STORE, 'w', encoding='utf-8', newline='\n').write('{\n' + ',\n'.join(lines) + '\n}\n')


class History:
    """Dates a page from git when the store does not know it: the newest commit that changed its fingerprint."""

    def __init__(self):
        self.cat = None

    def blob(self, sha, path):
        if self.cat is None:
            self.cat = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.cat.stdin.write(f'{sha}:{path}\n'.encode())
        self.cat.stdin.flush()
        header = self.cat.stdout.readline().decode().split()
        if len(header) < 3 or header[1] == 'missing':
            return None
        data = self.cat.stdout.read(int(header[2]))
        self.cat.stdout.read(1)
        return data.decode('utf-8', 'replace')

    def date(self, path, fp):
        try:
            log = subprocess.run(['git', 'log', '--format=%H %cI', '--', path], capture_output=True, text=True,
                                 check=True).stdout.split('\n')
        except (OSError, subprocess.CalledProcessError):
            return now()
        since = None
        for line in filter(None, log):
            sha, date = line.split(' ', 1)
            old = self.blob(sha, path)
            if old is None or fingerprint(old) != fp:
                break
            since = date
        return since or now()  # no commit carries this content yet: it is new in the working tree


def main():
    store, history, seen = load_store(), History(), set()

    def dated(url, path):
        """(sitemap entry, lastmod) for a URL served from a built file."""
        key = url[len(SITE):]
        fp = fingerprint(open(path, encoding='utf-8', errors='replace').read())
        old = store.get(key)
        if old and old.get('fp') == fp:
            lm = old['lastmod']
        elif old:
            lm = now()  # the store knew the page and its content changed
        else:
            lm = history.date(path, fp)
        store[key] = {'fp': fp, 'lastmod': lm}
        seen.add(key)
        return entry(url, lm, page_images(path) if key.startswith('/guide/') else ()), lm

    # ---- pages: the homepage, the hubs, every content/pages entry that was rendered, /contact/, /about/, buyer pages
    page_entries = [dated(SITE + '/', 'index.html')]
    for hub in ('advisory', 'projects', 'guide'):
        if os.path.exists(os.path.join(hub, 'index.html')):
            page_entries.append(dated(f'{SITE}/{hub}/', f'{hub}/index.html'))
    for f in sorted(glob.glob('content/pages/*.json')):
        rel = json.load(open(f, encoding='utf-8'))['path'].strip('/')
        if os.path.exists(os.path.join(rel, 'index.html')):
            page_entries.append(dated(f'{SITE}/{rel}/', f'{rel}/index.html'))
    for rel in ('contact', 'about'):  # real pages since 2026-09-29, written by build-site-pages.py
        if os.path.exists(os.path.join(rel, 'index.html')):
            page_entries.append(dated(f'{SITE}/{rel}/', f'{rel}/index.html'))
    for f in sorted(glob.glob('content/variants/*.json')):  # rendered by build-home.py at /<path>/
        rel = json.load(open(f, encoding='utf-8'))['path'].strip('/')
        if os.path.exists(os.path.join(rel, 'index.html')):
            page_entries.append(dated(f'{SITE}/{rel}/', f'{rel}/index.html'))
    pages_lm = write_sitemap('sitemap-pages.xml', page_entries)

    # ---- radar: the archive, then every post by its own dateModified
    _, posts = sc.read_posts()
    posts = sorted(posts, key=lambda x: x['datePublished'], reverse=True)
    latest = max(p['dateModified'] for p in posts)
    radar_entries = [(entry(f'{SITE}/radar/', latest), latest)]
    for p in posts:
        radar_entries.append((entry(f"{SITE}/radar/{p['slug']}/", p['dateModified']), p['dateModified']))
    radar_lm = write_sitemap('sitemap-radar.xml', radar_entries)

    # ---- museum: its static, crawlable pages (generated by museum/tools/build_artist_pages.py)
    museum_entries = []
    for rel, url in [('museum/index.html', f'{SITE}/museum/'), ('museum/artists/index.html', f'{SITE}/museum/artists/')]:
        if os.path.exists(rel):
            museum_entries.append(dated(url, rel))
    for mp in sorted(glob.glob('museum/artists/*/index.html')):
        mp = mp.replace('\\', '/')
        museum_entries.append(dated(f"{SITE}/museum/artists/{mp.split('/')[2]}/", mp))
    museum_lm = write_sitemap('sitemap-museum.xml', museum_entries)

    # a URL that left the sitemaps leaves the store
    save_store({k: v for k, v in store.items() if k in seen})

    # ---- the index
    def child(name, lm):
        l = f'\n    <lastmod>{lm}</lastmod>' if lm else ''
        return f'  <sitemap>\n    <loc>{SITE}/{name}</loc>{l}\n  </sitemap>'
    index = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
             + '\n'.join([child('sitemap-pages.xml', pages_lm), child('sitemap-radar.xml', radar_lm), child('sitemap-museum.xml', museum_lm)])
             + '\n</sitemapindex>\n')
    sc.write('sitemap.xml', index)
    print(f'sitemap.xml: index over sitemap-pages.xml ({len(page_entries)} URLs), sitemap-radar.xml ({len(radar_entries)}), sitemap-museum.xml ({len(museum_entries)})')


GUIDE_PHOTO = re.compile(r'<img\b[^>]*?\bsrc="(/images/(?:spaces|guides)/[^"]+?)(?:-1000)?\.webp"')


def page_images(path):
    """A guide's proposal photos for the image sitemap (2026-10-10): the after of its before/after pair and every
    photo in its body, each once, at its full 1800 px size; the bare before and the diagrams are left out."""
    html = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for src in GUIDE_PHOTO.findall(html):
        if src.endswith('_before') or src in out or not os.path.exists(src.lstrip('/') + '.webp'):
            continue
        out.append(src)
    return [SITE + s + '.webp' for s in out]


def entry(url, lastmod, images=()):
    lm = f'\n    <lastmod>{lastmod}</lastmod>' if lastmod else ''
    im = ''.join(f'\n    <image:image>\n      <image:loc>{i}</image:loc>\n    </image:image>' for i in images)
    return f'  <url>\n    <loc>{url}</loc>{lm}{im}\n  </url>'


def write_sitemap(name, entries):
    ns = ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' if '<image:image>' in ''.join(e for e, _ in entries) else ''
    text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"{ns}>\n'
            + '\n'.join(e for e, _ in entries) + '\n</urlset>\n')
    sc.write(name, text)
    dates = [d for _, d in entries if d]
    return max(dates) if dates else None


if __name__ == '__main__':
    main()
