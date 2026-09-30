#!/usr/bin/env python3
"""IndexNow after a deploy: tell Bing (and through it ChatGPT search and Perplexity) which
pages changed. The key file at the repo root is public by design (AGENTS.md, 2026-07-01).

    python3 tools/indexnow.py --since <sha>        every .html changed since that commit
    python3 tools/indexnow.py --urls /radar/x/ /   explicit paths or full URLs
    python3 tools/indexnow.py --all                every URL in the sitemaps

Each changed file maps to its live URL (radar/<slug>/index.html -> /radar/<slug>/); the
redirect stubs, 404.html and every noindex page are skipped (the buyer variants are
indexable since 2026-09-28 and are pinged like any other page). The script waits until every URL answers 200 on
the live site (GitHub Pages deploys in about a minute; --wait seconds, default 600), then
POSTs one batch to api.indexnow.org with the key and its keyLocation. Exit 1 if a URL never
went live or the API refused the batch. --dry-run prints the batch and stops.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = 'https://stavtheodor.com'
HOST = 'stavtheodor.com'
STUBS = ('2', 'our-team', 'our-team-1', 'questions', 'services', 'portfolio', 'blog')  # /about/ and /contact/ are real pages since 2026-09-29
KEY_FILE = glob.glob('*.txt')


def key():
    for f in sorted(glob.glob('[0-9a-f]' * 32 + '.txt')):
        return open(f, encoding='utf-8').read().strip()
    raise SystemExit('indexnow: no key file (32 hex characters .txt) at the repo root')


def url_for(path):
    """A file in the tree to its live URL, or None when it is not an indexable page."""
    path = path.replace('\\', '/')
    if path == 'index.html':
        url = SITE + '/'
    # site URLs are directory index pages; templates/, content/ and the stubs are not pages
    elif not path.endswith('/index.html') or path.split('/')[0] in STUBS + ('templates', 'content', 'museum'):
        return None
    else:
        url = f'{SITE}/{path[:-len("index.html")]}'
    # a noindex page is never pinged (the buyer variants are indexable since 2026-09-28, Ron)
    if os.path.exists(path) and 'name="robots" content="noindex"' in open(path, encoding='utf-8', errors='replace').read():
        return None
    return url


def changed_since(sha):
    out = subprocess.run(['git', 'diff', '--name-only', f'{sha}..HEAD', '--', '*.html'], capture_output=True, text=True, check=True).stdout
    urls = [url_for(p) for p in out.split()]
    return sorted({u for u in urls if u and os.path.exists(u.replace(SITE + '/', '') + 'index.html' if u.endswith('/') else u.replace(SITE + '/', ''))})


def sitemap_urls():
    locs = lambda text: re.findall(r'<loc>([^<]+)</loc>', text)
    index = open('sitemap.xml', encoding='utf-8').read()
    if '<sitemapindex' not in index:
        return locs(index)
    urls = []
    for child in locs(index):
        urls += locs(open(child.replace(SITE + '/', ''), encoding='utf-8').read())
    return urls


def status(url):
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'theodora-indexnow/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def wait_live(urls, seconds):
    pending, deadline = list(urls), time.time() + seconds
    while pending and time.time() < deadline:
        pending = [u for u in pending if status(u) != 200]
        if pending:
            time.sleep(15)
    return pending


def submit(urls, k):
    payload = json.dumps({'host': HOST, 'key': k, 'keyLocation': f'{SITE}/{k}.txt', 'urlList': urls}).encode()
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=payload, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.reason
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:200]


def main():
    ap = argparse.ArgumentParser(description='IndexNow ping for stavtheodor.com')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--since', metavar='SHA', help='every .html changed since this commit')
    g.add_argument('--urls', nargs='+', metavar='URL', help='paths (/radar/x/) or full URLs')
    g.add_argument('--all', action='store_true', help='every URL in the sitemaps')
    ap.add_argument('--wait', type=int, default=600, help='seconds to wait for every URL to answer 200 (default 600)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    if a.since:
        urls = changed_since(a.since)
    elif a.all:
        urls = sitemap_urls()
    else:
        urls = [u if u.startswith('http') else SITE + '/' + u.lstrip('/') for u in a.urls]
    if not urls:
        print('indexnow: nothing to submit')
        return
    print(f'indexnow: {len(urls)} URL(s)')
    if a.dry_run:
        print('\n'.join(urls))
        return
    k = key()
    late = wait_live(urls, a.wait)
    if late:
        print('indexnow: not live after the wait, not submitted:\n' + '\n'.join(late))
        sys.exit(1)
    code, reason = submit(urls, k)
    print(f'indexnow: {code} {reason} for {len(urls)} URL(s)')
    if code not in (200, 202):
        sys.exit(1)


if __name__ == '__main__':
    main()
