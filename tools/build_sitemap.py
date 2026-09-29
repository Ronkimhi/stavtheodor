#!/usr/bin/env python3
"""sitemap.xml for stavtheodor.com: a sitemap index over three child sitemaps (2026-09-26).

  sitemap-pages.xml    the homepage, the two hubs, every advisory, project, partner, guide and
                       local landing page (content/pages/*.json), /contact/ and /about/ (since 2026-09-29), and the
                       buyer pages (content/variants/*.json, indexable since 2026-09-28)
  sitemap-radar.xml    the Art Radar archive and every post (content/posts.html)
  sitemap-museum.xml   the Museum's static pages (museum/index.html, museum/artists/, one
                       page per artist), which used to dilute one flat sitemap

lastmod comes from one `git log --format=%cI --name-only` pass, keyed on each page's source:
content/pages/<slug>.json for a growth page (the homepage and the hubs take the newest of
their sources), a buyer page's JSON, its images and the homepage template it is rendered from, the post's own dateModified for a post, and the museum file itself. With no
git available lastmod is omitted rather than invented. Run by python3 build.py after the
pages are written; run it alone from the repo root after editing content.
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import site_chrome as sc  # noqa: E402
from site_chrome import SITE  # noqa: E402

os.chdir(ROOT)
DATE_LINE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
HOME_SOURCES = ['templates/home.html', 'content/faq.json', 'content/entity.json', 'content/posts.html', 'build-home.py']


def git_dates():
    """{path: committer date of the newest commit touching it}, or None without git."""
    try:
        out = subprocess.run(['git', 'log', '--format=%cI', '--name-only'], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    dates, current = {}, None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if DATE_LINE.match(line):
            current = line
        elif current:
            dates.setdefault(line.replace('\\', '/'), current)
    return dates


def newest(dates, sources):
    if dates is None:
        return None
    found = [dates[s] for s in sources if s in dates]
    return max(found) if found else None


def entry(url, lastmod):
    lm = f'\n    <lastmod>{lastmod}</lastmod>' if lastmod else ''
    return f'  <url>\n    <loc>{url}</loc>{lm}\n  </url>'


def write_sitemap(name, entries):
    text = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + '\n'.join(e for e, _ in entries) + '\n</urlset>\n')
    sc.write(name, text)
    dates = [d for _, d in entries if d]
    return max(dates) if dates else None


def main():
    dates = git_dates()
    if dates is None:
        print('build_sitemap: git unavailable, lastmod omitted')

    # ---- pages: the homepage, the hubs, every content/pages entry that was rendered
    pages = []
    for f in sorted(glob.glob('content/pages/*.json')):
        p = json.load(open(f, encoding='utf-8'))
        rel = p['path'].strip('/')
        if os.path.exists(os.path.join(rel, 'index.html')):
            pages.append((p, f.replace('\\', '/')))
    home_lm = newest(dates, HOME_SOURCES + [src for _, src in pages])
    page_entries = [(entry(SITE + '/', home_lm), home_lm)]
    for hub, sections in (('advisory', ('local', 'area', 'advisory')), ('projects', ('projects',))):
        if os.path.exists(os.path.join(hub, 'index.html')):
            lm = newest(dates, [src for p, src in pages if p['section'] in sections])
            page_entries.append((entry(f'{SITE}/{hub}/', lm), lm))
    for p, src in pages:
        lm = newest(dates, [src])
        page_entries.append((entry(f"{SITE}/{p['path'].strip('/')}/", lm), lm))
    # /contact/, a real page since 2026-09-29 (Ron's SEO brief, P1.1), written by build-site-pages.py (CONTACT)
    if os.path.exists(os.path.join('contact', 'index.html')):
        lm = newest(dates, ['build-site-pages.py'])
        page_entries.append((entry(f'{SITE}/contact/', lm), lm))
    # /about/, a real page since 2026-09-29 (in place of the redirect stub to /#about), written by build-site-pages.py (ABOUT)
    # from the homepage template and the partner pages' JSON, so it moves with any of them
    if os.path.exists(os.path.join('about', 'index.html')):
        lm = newest(dates, ['build-site-pages.py', 'templates/home.html', 'content/pages/for-designers.json',
                            'content/pages/for-brokers.json', 'content/pages/for-advisors.json'])
        page_entries.append((entry(f'{SITE}/about/', lm), lm))
    # the buyer pages (content/variants/<id>.json, rendered by build-home.py at /<path>/)
    for f in sorted(glob.glob('content/variants/*.json')):
        v = json.load(open(f, encoding='utf-8'))
        rel = v['path'].strip('/')
        if not os.path.exists(os.path.join(rel, 'index.html')):
            continue
        images = sorted(g.replace('\\', '/') for g in glob.glob(f"images/home2/variants/{v['id']}/*"))
        lm = newest(dates, [f.replace('\\', '/'), 'templates/home.html', 'build-home.py'] + images)
        page_entries.append((entry(f'{SITE}/{rel}/', lm), lm))
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
            lm = newest(dates, [rel])
            museum_entries.append((entry(url, lm), lm))
    for mp in sorted(glob.glob('museum/artists/*/index.html')):
        mp = mp.replace('\\', '/')
        slug = mp.split('/')[2]
        lm = newest(dates, [mp])
        museum_entries.append((entry(f'{SITE}/museum/artists/{slug}/', lm), lm))
    museum_lm = write_sitemap('sitemap-museum.xml', museum_entries)

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


if __name__ == '__main__':
    main()
