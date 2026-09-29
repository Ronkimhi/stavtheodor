#!/usr/bin/env python3
"""Asks every sameAs URL in content/entity.json whether it still answers (Ron's SEO brief, 2026-09-29, P0.4).

    python3 tools/check_sameas.py            # print the ones that fail, always exit 0 (python3 build.py runs it)
    python3 tools/check_sameas.py --strict   # exit 1 when one fails

A HEAD first, then a GET if HEAD is refused. Yelp and Trustpilot answer scripts with 403, Alignable with 429,
and some profile sites block every bot the same way: those codes count as alive. Without a network the check
says so and moves on; it never blocks a build, a dead profile is a listing to fix, not a page to hold back.
"""
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOT_BLOCKED = {401, 403, 405, 429, 999}  # alive, the site just refuses scripts (LinkedIn answers 999)
BOT_HOSTS = ('facebook.com', 'linkedin.com', 'instagram.com')  # any 4xx from these is their bot wall, not a dead page
# Certificates are verified, but not with Python 3.13's strict X.509 flag: several CDNs (Facebook, Substack)
# serve chains it rejects ("Missing Authority Key Identifier") that every browser accepts.
CTX = ssl.create_default_context()
CTX.verify_flags &= ~getattr(ssl, 'VERIFY_X509_STRICT', 0)
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'


def urls():
    graph = json.load(open(os.path.join(ROOT, 'content', 'entity.json'), encoding='utf-8'))['@graph']
    return [(n.get('@id', n.get('@type')), u) for n in graph for u in n.get('sameAs') or []]


def probe(u):
    for method in ('HEAD', 'GET'):
        req = urllib.request.Request(u, method=method, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=12, context=CTX) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == 'HEAD' and e.code in (404, 405, 403, 400, 501):
                continue  # some sites refuse HEAD only
            return e.code
        except Exception as e:  # DNS, timeout, TLS: no answer at all
            return f'no answer ({type(e).__name__})'
    return 'no answer'


def main():
    todo = urls()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda x: (x[0], x[1], probe(x[1])), todo))
    offline = all(isinstance(code, str) for _, _, code in results)
    if offline:
        print(f'check_sameas: no network, {len(todo)} sameAs URL(s) not checked')
        return 0
    def alive(u, code):
        return isinstance(code, int) and (code < 400 or code in BOT_BLOCKED or (code < 500 and any(h in u for h in BOT_HOSTS)))
    bad = [(who, u, code) for who, u, code in results if not alive(u, code)]
    for who, u, code in bad:
        print(f'check_sameas: {who} sameAs {u} -> {code}')
    print(f'check_sameas: {len(todo) - len(bad)} of {len(todo)} sameAs URL(s) answer')
    return 1 if (bad and '--strict' in sys.argv) else 0


if __name__ == '__main__':
    sys.exit(main())
