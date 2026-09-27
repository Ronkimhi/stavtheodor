#!/usr/bin/env python3
"""Build the homepage, index.html, from templates/home.html and the site's data.

  templates/home.html   the approved design (the ArtLink register, v3, 2026-09-26) with slots
  content/posts.html    the six newest posts fill the Art Radar timeline
  content/pages/*.json  the six lead projects and the advisory rows
  content/faq.json      the seven questions: visible FAQ and FAQPage schema, the same text
  content/entity.json   the Person + ProfessionalService + WebSite graph
  site_chrome.py        nav, footer, switch, mailto fallback, GA, the <head>

Also writes the /2/ redirect stubs (the second homepage lived there while it was being
approved; every /2/ address now forwards to its real page), and the buyer variants
(2026-09-27): each content/variants/<id>.json renders this same page at /<path>/ with its
own copy in the sixteen regions the template marks <!--variant:NAME-->...<!--/variant:NAME-->,
its own questions, closing line and mail subject. Variants are noindex, in no sitemap and
linked from nowhere (content/VARIANT-SPEC.md); the homepage keeps the text between the markers.

Never hand-edit index.html or a variant folder: run python3 build.py (or this script) after
editing any of the files above. The build refuses to run if a post was pasted into index.html.
"""
import collections
import json
import os
import re
import sys
import html as H

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc
from site_chrome import SITE, T

TEMPLATE = sc.rel('templates', 'home.html')
VARIANTS_DIR = sc.rel('content', 'variants')
TITLE = 'Art Curator & Advisor · New Jersey, New York, Tel Aviv | THEODORA'
DESCRIPTION = 'Stav Theodor, art curator and advisor in Tenafly, New Jersey: art for homes and businesses in Bergen County, Manhattan, New York and Tel Aviv, from concept to installation.'
OG_TITLE = 'Stav Theodor-Kimhi · Art Curator & Advisor'
OG_DESC = 'Art for homes and businesses in New York, New Jersey and Tel Aviv, from concept to installation.'
OG_IMAGE = SITE + '/og-home.jpg'
OG_IMAGE_ALT = 'Stav Theodor-Kimhi, art curator, beside the THEODORA mark'
# the opening's first texture pair, fetched with high priority (speed pass, 2026-09-26)
PRELOAD = ('<link rel="preload" as="image" href="/images/home2/pairs/p3_before.webp" type="image/webp" fetchpriority="high">\n'
           '<link rel="preload" as="image" href="/images/home2/pairs/p3_after.webp" type="image/webp" fetchpriority="high">\n')

PROJECT_ORDER = [
    'caesarea-garden-villa', 'caesarea-sea-view-villa-triptych', 'closter-new-jersey-new-construction',
    'herzliya-pituach-sea-view-apartment', 'hod-hasharon-private-villa', 'ramat-gan-private-home',
]
ADVISORY_HUBS = {
    '/advisory/': ('Art advisory, answered plainly: what it costs, how it works, where I work', 'ייעוץ אמנות בשפה פשוטה: כמה זה עולה, איך זה עובד, ואיפה אני עובדת'),
    '/projects/': ('Projects: homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels, one exhibition in Geneva', "פרויקטים: בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות, ותערוכה אחת בז'נבה"),
}
# The homepage's Advisory rows in order: the two local landing pages first (2026-09-26), the two hubs,
# the partner pages and the guide. A variant may list its own (advisory_rows): content/pages paths and the hubs.
HOME_ROWS = ['art-curator-new-jersey', 'art-curator-new-york', '/advisory/', '/projects/',
             'for-designers', 'for-brokers', 'for-advisors', 'guide/ten-questions-before-you-buy-your-first-serious-artwork']

# The sixteen regions templates/home.html marks for the buyer variants, and the variant field each one reads
# (services_N reads services[N-1].desc_en and desc_he; the others read <object>.<field>_en and _he).
REGIONS = {
    'hero_l1': ('hero', 'l1'), 'hero_l2': ('hero', 'l2'),
    'intro_h1': ('intro', 'h1'), 'intro_line': ('intro', 'line'), 'intro_eyebrow': ('intro', 'eyebrow'),
    'intro_statement': ('intro', 'statement'),
    'services_1': ('services', 0), 'services_2': ('services', 1), 'services_3': ('services', 2), 'services_4': ('services', 3),
    'what_i_do_eyebrow': ('what_i_do', 'eyebrow'), 'what_i_do_h2': ('what_i_do', 'h2'),
    'what_i_do_p1': ('what_i_do', 'p1'), 'what_i_do_p2': ('what_i_do', 'p2'),
    'advisory_h2': ('advisory', 'h2'), 'advisory_sub': ('advisory', 'sub'),
}
OPTIONAL = {'intro_eyebrow', 'what_i_do_eyebrow', 'advisory_h2', 'advisory_sub'}  # absent: the homepage text stays
HTML_REGIONS = {'what_i_do_p1', 'what_i_do_p2'}  # a, em and strong allowed (tools/check_variants.py); the rest is escaped
MARK = re.compile(r'<!--variant:([a-z0-9_]+)-->(.*?)<!--/variant:\1-->', re.S)
ANCHORS = ('about', 'what-i-do', 'portfolio', 'film', 'projects', 'advisory', 'museum', 'radar', 'posts', 'faq', 'contact')
SHARED_SECTIONS = ('about', 'film', 'projects', 'museum', 'radar')  # byte for byte the homepage's on every variant
VARIANT_PATH = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)?$')


def load_pages():
    pages = {}
    for f in sorted(os.listdir(sc.rel('content', 'pages'))):
        if f.endswith('.json'):
            d = json.load(open(sc.rel('content', 'pages', f), encoding='utf-8'))
            pages[d['path'].strip('/')] = d
    return pages


def load_variants(home_faq):
    """content/variants/<id>.json in file-name order, [] without the folder. A FAQ item
    {"home": "<q_en>"} is the homepage question with that English text (content/faq.json)."""
    if not os.path.isdir(VARIANTS_DIR):
        return []
    by_question = {q['q_en']: q for q in home_faq}
    variants = []
    for f in sorted(os.listdir(VARIANTS_DIR)):
        if not f.endswith('.json'):
            continue
        v = json.load(open(os.path.join(VARIANTS_DIR, f), encoding='utf-8'))
        where = f'content/variants/{f}'
        if v.get('id') != f[:-len('.json')] or not VARIANT_PATH.match(v.get('path') or ''):
            raise SystemExit(f'{where}: bad id or path (run python3 tools/check_variants.py {where})')
        faq = []
        for item in v.get('faq') or []:
            if 'home' in item:
                if item['home'] not in by_question:
                    raise SystemExit(f'{where}: the FAQ reference {item["home"]!r} is no longer a question in content/faq.json')
                faq.append(by_question[item['home']])
            else:
                faq.append(item)
        v['faq'] = faq
        variants.append(v)
    return variants


def advisory_rows(pages, paths):
    """The Advisory rows: a content/pages path is a row with that page's title; /advisory/ and
    /projects/ are the two hubs with their own line."""
    rows = ''
    for path in paths:
        hub = '/' + path.strip('/') + '/'
        if hub in ADVISORY_HUBS:
            en, he = ADVISORY_HUBS[hub]
            rows += f'<a class="row" href="{hub}"><h3 class="serif">{T(en, he)}</h3><span class="ln"></span></a>'
            continue
        d = pages[path.strip('/')]
        rows += f'<a class="row" href="/{path.strip("/")}/"><h3 class="serif">{T(H.escape(d["title_en"]), H.escape(d["title_he"]))}</h3><span class="ln"></span></a>'
    return rows


def region_copy(v, name):
    """A variant's (en, he) for one marked region, or None when an optional field is absent."""
    obj, key = REGIONS[name]
    if obj == 'services':
        d, key = v['services'][key], 'desc'
    else:
        d = v.get(obj) or {}
    if not d.get(key + '_en'):
        if name in OPTIONAL:
            return None
        raise SystemExit(f"content/variants/{v['id']}.json: {obj}.{key}_en is missing")
    return d[key + '_en'], d[key + '_he']


def fill_regions(body, v):
    """The marked regions: the template's own text for the homepage (the markers go, the bytes
    between them stay), the variant's copy otherwise. Every region must appear exactly once."""
    seen = collections.Counter()

    def fill(m):
        name, inner = m.group(1), m.group(2)
        seen[name] += 1
        pair = region_copy(v, name) if v is not None and name in REGIONS else None
        if pair is None:
            return inner
        en, he = pair
        return T(en, he) if name in HTML_REGIONS else T(H.escape(en), H.escape(he))

    body = MARK.sub(fill, body)
    assert set(seen) == set(REGIONS) and all(n == 1 for n in seen.values()), f'variant regions in the template: {dict(seen)}'
    assert '<!--variant:' not in body and '<!--/variant:' not in body, 'a variant marker was left in the page'
    return body


def render_home(pages, posts, faq, v=None):
    """The homepage, or with v (a loaded variant) the same page with the variant's copy at /<path>/."""
    tmpl = open(TEMPLATE, encoding='utf-8').read()
    projects = [pages['projects/' + s] for s in PROJECT_ORDER]
    subject = v['mail_subject'] if v else ''
    questions = v['faq'] if v else faq
    fills = {
        'NAV': sc.nav(home=True),
        'PROJECT_CARDS': ''.join(sc.project_card(p) for p in projects),
        'ADVISORY_ROWS': advisory_rows(pages, (v.get('advisory_rows') if v else None) or HOME_ROWS),
        'TIMELINE': sc.timeline(posts[:6], with_months=False),
        'POST_COUNT': str(len(posts)),
        'FAQ': sc.faq_details(questions, first_open=True),
        'FOOTER': sc.footer(home=True, cta=(v['cta_en'], v['cta_he']) if v else None, subject=subject),
        'MAIL_UI': sc.mail_ui(subject),
        'LANG_JS': sc.LANG_JS,
        'PAGE_JS': sc.PAGE_JS,
    }
    body = tmpl
    for k, val in fills.items():
        n = body.count('{{' + k + '}}')
        assert n == (2 if k == 'POST_COUNT' else 1), f'slot {k} appears {n} times in the template'
        body = body.replace('{{' + k + '}}', val)
    assert '{{' not in body, 'unfilled slot'
    body = fill_regions(body, v)
    meta = v['head'] if v else {'title': TITLE, 'description': DESCRIPTION, 'og_title': OG_TITLE, 'og_description': OG_DESC}
    url = f"{SITE}/{v['path']}/" if v else SITE + '/'  # a variant is its own canonical, and noindex
    head = sc.head(meta['title'], meta['description'], url, og_title=meta['og_title'], og_desc=meta['og_description'],
                   og_image=OG_IMAGE, og_card_dims=True, og_image_alt=OG_IMAGE_ALT, lang='en', ld=[sc.faq_schema(questions)],
                   noindex=bool(v), extra=PRELOAD)
    return head + body


def section(page, sid):
    m = re.search(r'<section\b[^>]*\bid="' + sid + r'"[^>]*>.*?</section>', page, re.S)
    return m.group(0) if m else None


def page_problems(out, name, home=None):
    """What stops a page from being written. With home (the rendered homepage), out is a variant:
    it must also be noindex and carry the shared sections exactly as the homepage does."""
    problems = []
    if re.search('[\\u2013\\u2014]', re.sub(r'<script.*?</script>', '', out, flags=re.S)):
        problems.append(f'em or en dash in {name}')
    en, he = out.count('data-l="en"'), out.count('data-l="he"')
    if en != he:
        problems.append(f'twins differ in {name}: {en} en, {he} he')
    for anchor in ANCHORS:
        if f'id="{anchor}"' not in out:
            problems.append(f'anchor #{anchor} missing')
    if home is not None:
        if '<meta name="robots" content="noindex">' not in out:
            problems.append(f'{name} is not noindex')
        for sid in SHARED_SECTIONS:
            mine = section(out, sid)
            if mine is None or mine != section(home, sid):
                problems.append(f'section #{sid} differs from the homepage')
    return problems


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


def write_variants(pages, posts, faq, home):
    """Every variant at <path>/index.html, or none: all are rendered and checked before the first is
    written. A variant never overwrites a file that is not a variant page (one without data-subject)."""
    ready = []
    for v in load_variants(faq):
        rel_path = f"{v['path']}/index.html"
        out = render_home(pages, posts, faq, v)
        problems = page_problems(out, rel_path, home)
        full = sc.rel(rel_path)
        if os.path.exists(full) and 'data-subject="' not in open(full, encoding='utf-8').read():
            problems.append(f'{rel_path} exists and is not a variant page')
        if problems:
            raise SystemExit(f'{rel_path} NOT written, and no variant was: ' + '; '.join(problems))
        ready.append((rel_path, out))
    for rel_path, out in ready:
        sc.write(rel_path, out)
    return [rel_path for rel_path, _ in ready]


def main():
    sc.guard_index()
    pages = load_pages()
    _, posts = sc.read_posts()
    faq = sc.load_faq()
    out = render_home(pages, posts, faq)
    problems = page_problems(out, 'index.html')
    if problems:
        raise SystemExit('index.html NOT written: ' + '; '.join(problems))
    sc.write('index.html', out)
    stubs = write_redirects(pages)
    print(f'wrote index.html ({len(posts)} posts, timeline shows {min(6, len(posts))}, {len(faq)} questions) and {len(stubs)} redirect stubs (/2/ and the old Squarespace paths)')
    written = write_variants(pages, posts, faq, out)
    print(f'wrote {len(written)} buyer variant(s) from content/variants/' + (': ' + ', '.join('/' + p[:-len('index.html')] for p in written) if written else ''))


if __name__ == '__main__':
    main()
