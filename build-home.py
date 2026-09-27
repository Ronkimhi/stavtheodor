#!/usr/bin/env python3
"""Build the homepage, index.html, from templates/home.html and the site's data.

  templates/home.html   the approved design (the ArtLink register, v3, 2026-09-26) with slots
  content/posts.html    the six newest posts fill the Art Radar timeline
  content/pages/*.json  the six lead projects and the advisory rows
  content/faq.json      the seven questions: visible FAQ and FAQPage schema, the same text
  content/entity.json   the Person + ProfessionalService + WebSite graph
  site_chrome.py        nav, footer, switch, mailto fallback, GA, the <head>

Also writes the /2/ redirect stubs (the second homepage lived there while it was being
approved; every /2/ address now forwards to its real page).

Never hand-edit index.html: run python3 build.py (or this script) after editing any of
the files above. The build refuses to run if a post was pasted into index.html.
"""
import json
import os
import re
import sys
import html as H

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc
from site_chrome import SITE, T

TEMPLATE = sc.rel('templates', 'home.html')
TITLE = 'Art Curator & Advisor · New Jersey, New York, Tel Aviv | THEODORA'
DESCRIPTION = 'Stav Theodor, art curator and advisor in Tenafly, New Jersey: art for homes and businesses in Bergen County, Manhattan, New York and Tel Aviv, from concept to installation.'
OG_TITLE = 'Art Radar · Stav Theodor-Kimhi'
OG_DESC = 'The art worth seeing, chosen by a curator. Exhibitions, openings, and the stories behind them, and the art I help people live with.'
OG_IMAGE_ALT = 'Stav Theodor-Kimhi, art curator, beside the THEODORA mark'

PROJECT_ORDER = [
    'caesarea-garden-villa', 'caesarea-sea-view-villa-triptych', 'closter-new-jersey-new-construction',
    'herzliya-pituach-sea-view-apartment', 'hod-hasharon-private-villa', 'ramat-gan-private-home',
]
LOCAL_PAGES = ['art-curator-new-jersey', 'art-curator-new-york']  # the first two Advisory rows (2026-09-26)
ADVISORY_HUBS = [
    ('/advisory/', 'Art advisory, answered plainly: what it costs, how it works, where I work', 'ייעוץ אמנות בשפה פשוטה: כמה זה עולה, איך זה עובד, ואיפה אני עובדת'),
    ('/projects/', 'Projects: homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels, one exhibition in Geneva', "פרויקטים: בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות, ותערוכה אחת בז'נבה"),
]
ADVISORY_PAGES = ['for-designers', 'for-brokers', 'for-advisors', 'guide/ten-questions-before-you-buy-your-first-serious-artwork']


def load_pages():
    pages = {}
    for f in sorted(os.listdir(sc.rel('content', 'pages'))):
        if f.endswith('.json'):
            d = json.load(open(sc.rel('content', 'pages', f), encoding='utf-8'))
            pages[d['path'].strip('/')] = d
    return pages


def render_home(pages, posts, faq):
    tmpl = open(TEMPLATE, encoding='utf-8').read()
    projects = [pages['projects/' + s] for s in PROJECT_ORDER]
    rows = ''
    for path in LOCAL_PAGES + [None] + ADVISORY_PAGES:
        if path is None:
            rows += ''.join(f'<a class="row" href="{h}"><h3 class="serif">{T(en, he)}</h3><span class="ln"></span></a>' for h, en, he in ADVISORY_HUBS)
            continue
        d = pages[path]
        rows += f'<a class="row" href="/{path}/"><h3 class="serif">{T(H.escape(d["title_en"]), H.escape(d["title_he"]))}</h3><span class="ln"></span></a>'
    fills = {
        'NAV': sc.nav(home=True),
        'PROJECT_CARDS': ''.join(sc.project_card(p) for p in projects),
        'ADVISORY_ROWS': rows,
        'TIMELINE': sc.timeline(posts[:6], with_months=False),
        'POST_COUNT': str(len(posts)),
        'FAQ': sc.faq_details(faq, first_open=True),
        'FOOTER': sc.footer(home=True),
        'MAIL_UI': sc.MAIL_UI,
        'LANG_JS': sc.LANG_JS,
        'PAGE_JS': sc.PAGE_JS,
    }
    body = tmpl
    for k, v in fills.items():
        n = body.count('{{' + k + '}}')
        assert n == (2 if k == 'POST_COUNT' else 1), f'slot {k} appears {n} times in the template'
        body = body.replace('{{' + k + '}}', v)
    assert '{{' not in body, 'unfilled slot'
    head = sc.head(TITLE, DESCRIPTION, SITE + '/', og_title=OG_TITLE, og_desc=OG_DESC, og_card_dims=True,
                   og_image_alt=OG_IMAGE_ALT, lang='en', ld=[sc.faq_schema(faq)],
                   extra='<link rel="preload" as="image" href="/images/home2/pairs/p3_after.webp" type="image/webp">\n')
    return head + body


OLD_PATHS = {  # Squarespace-era addresses that still rank or sit in old links: one consistent stub each
    'about': (SITE + '/#about', 'About Stav Theodor-Kimhi, Art Curator and Advisor | THEODORA'),
    'our-team': (SITE + '/#about', 'About Stav Theodor-Kimhi, Art Curator and Advisor | THEODORA'),
    'our-team-1': (SITE + '/#about', 'About Stav Theodor-Kimhi, Art Curator and Advisor | THEODORA'),
    'contact': (SITE + '/#contact', 'Contact Stav Theodor-Kimhi | THEODORA'),
    'questions': (SITE + '/#faq', 'Questions people ask before they write | THEODORA'),
}


def write_redirects(pages):
    """/2/ was the second homepage while it was being approved, and the old Squarespace paths
    still get visitors. Every address forwards: canonical, meta refresh, location.replace, noindex."""
    targets = {'2/index.html': SITE + '/', '2/projects/index.html': SITE + '/projects/', '2/radar/index.html': SITE + '/radar/'}
    for path in pages:
        if path.startswith('projects/'):
            targets[f'2/{path}/index.html'] = f'{SITE}/{path}/'
    for rel_path, target in targets.items():
        sc.write(rel_path, sc.redirect_stub(target))
    for d, (target, title) in OLD_PATHS.items():
        sc.write(f'{d}/index.html', sc.redirect_stub(target, title))
    return sorted(targets) + sorted(f'{d}/index.html' for d in OLD_PATHS)


def main():
    sc.guard_index()
    pages = load_pages()
    _, posts = sc.read_posts()
    faq = sc.load_faq()
    out = render_home(pages, posts, faq)
    problems = []
    if re.search('[\\u2013\\u2014]', re.sub(r'<script.*?</script>', '', out, flags=re.S)):
        problems.append('em or en dash in index.html')
    en, he = out.count('data-l="en"'), out.count('data-l="he"')
    if en != he:
        problems.append(f'twins differ in index.html: {en} en, {he} he')
    for anchor in ('about', 'what-i-do', 'portfolio', 'film', 'projects', 'advisory', 'museum', 'radar', 'posts', 'faq', 'contact'):
        if f'id="{anchor}"' not in out:
            problems.append(f'anchor #{anchor} missing')
    if problems:
        raise SystemExit('index.html NOT written: ' + '; '.join(problems))
    sc.write('index.html', out)
    stubs = write_redirects(pages)
    print(f'wrote index.html ({len(posts)} posts, timeline shows {min(6, len(posts))}, {len(faq)} questions) and {len(stubs)} redirect stubs (/2/ and the old Squarespace paths)')


if __name__ == '__main__':
    main()
