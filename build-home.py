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
its own value strip (a variant-only section under the intro block, 2026-09-28: the template's
marker is empty, so the homepage gets nothing there), its own questions, closing line and mail subject. Variants are indexable, each its own canonical
and listed in sitemap-pages.xml (Ron, 2026-09-28), and linked only from the homepage's #industries
section (content/VARIANT-SPEC.md); the homepage keeps the text between the markers.
A variant may also put its own rooms in the opening ("rooms", entry i in slot i): the page then
sets window.THEODORA_ROOMS for js/home-opening.js, preloads its first pair, and carries each
replaced slot's static figure and #cap caption (the room_fig_N, room_cap_N and rooms_js regions);
"head.og_image" gives it its own link preview.

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


def preload(before, after):
    """The opening's first texture pair, fetched with high priority (speed pass, 2026-09-26): the
    homepage's p3, or a variant's first room. The paths are under /images/home2/, as in PAIRS."""
    return ''.join(f'<link rel="preload" as="image" href="/images/home2/{n}" type="image/webp" fetchpriority="high">\n' for n in (before, after))


PRELOAD = preload('pairs/p3_before.webp', 'pairs/p3_after.webp')

# "Who I work with" on the homepage (Ron, 2026-09-28): one tile per buyer page, in this order, each linking to it.
# The tile's line is the page's main message, the first sentence of its intro statement (Ron's locked messaging),
# and its image images/home2/industries/<id>.webp, made from the page's first room by tools/make_industry_thumbs.py.
INDUSTRIES = [
    ('designers', 'Interior designers', 'מעצבי פנים'),
    ('law-firms', 'Law firms', 'משרדי עורכי דין'),
    ('investment-firms', 'Investment firms', 'חברות השקעה'),
    ('wealth-managers', 'Wealth managers', 'מנהלי הון'),
    ('hotels', 'Boutique hotels', 'מלונות בוטיק'),
    ('restaurants', 'Restaurants', 'מסעדות'),
    ('medical-practices', 'Clinics', 'מרפאות'),
]
INDUSTRY_THUMB = (600, 400)

# The six lead projects: each shows a photograph of its own (2026-09-28: Closter and Ramat Gan left this row when
# their Gemini-marked photos were removed; they come back when Stav sends clean photographs of them).
PROJECT_ORDER = [
    'caesarea-garden-villa', 'caesarea-sea-view-villa-triptych', 'herzliya-pituach-sea-view-apartment',
    'hod-hasharon-private-villa', 'tel-aviv-home-of-roni-daloomi', 'caesarea-private-estate',
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
# Variant-only blocks: the template's marker is empty, so the homepage renders nothing in its place and a
# variant renders the whole block. value_strip: the three columns right after #intro (2026-09-28).
BLOCKS = {'value_strip'}
# Homepage-only sections: the homepage keeps the bytes between the markers, every variant drops them.
# film: the 67 second film, aimed at designers and collectors, is off the buyer pages (Ron, 2026-09-28).
DROPS = {'film', 'industries'}
# industries: the homepage's links to the seven buyer pages (2026-09-28), never on a buyer page itself.
MARK = re.compile(r'<!--variant:([a-z0-9_]+)-->(.*?)<!--/variant:\1-->', re.S)
ANCHORS = ('about', 'what-i-do', 'portfolio', 'film', 'projects', 'advisory', 'museum', 'radar', 'posts', 'faq', 'contact')
SHARED_SECTIONS = ('about', 'projects', 'museum', 'radar')  # byte for byte the homepage's on every variant
VARIANT_ABSENT = ('film', 'industries')  # on the homepage, never on a variant (DROPS)
VARIANT_PATH = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)?$')

# The opening's rooms (2026-09-27). PAIRS in js/home-opening.js lists them in slot order (p3, p4, p5, p1): slot 0 is
# the first fold. templates/home.html marks each slot's static figure (room_fig_N) and the content of its #cap caption
# (room_cap_N), and an empty region before the deferred scripts (rooms_js). A variant's "rooms" (entry i replaces
# slot i) fill them; the homepage, and a variant without rooms, keep the bytes between the markers.
HOME_ROOMS = re.findall(r"cap: '(\w+)',[^\n]*?land: \{ b: '([^']+)', a: '([^']+)'",
                        open(sc.rel('js', 'home-opening.js'), encoding='utf-8').read())  # [(cap key, before, after)]
if not HOME_ROOMS:
    raise SystemExit('js/home-opening.js: no rooms read from PAIRS (did its format change?)')
ROOM_REGIONS = {f'room_{kind}_{i}' for kind in ('fig', 'cap') for i in range(len(HOME_ROOMS))} | {'rooms_js'}
ROOM_KEYS = ('b', 'a', 'w', 'h', 'rect', 'fx', 'fy', 'from')  # what js/home-opening.js takes from a room, plus seed


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
        rooms = v.get('rooms')
        if v.get('rooms_rest', 'drop') not in ('drop', 'home') or ('rooms_rest' in v and not rooms):
            raise SystemExit(f'{where}: rooms_rest is "drop" or "home", and only beside rooms (run python3 tools/check_variants.py {where})')
        if rooms is not None and not (isinstance(rooms, list) and 1 <= len(rooms) <= len(HOME_ROOMS) and all(
                isinstance(r, dict) and set(ROOM_KEYS + ('cap_en', 'cap_he', 'alt_en')) <= set(r) for r in rooms)):
            raise SystemExit(f'{where}: bad rooms (run python3 tools/check_variants.py {where})')
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


def first_sentence(s):
    """The main message: the statement's first sentence."""
    m = re.match(r'(.+?[.?!])(?:\s|$)', s)
    return m.group(1) if m else s


def industries(variants):
    """The homepage's industries section: one keyboard-focusable tile per buyer page, linking to it."""
    by_id = {v['id']: v for v in variants}
    missing = [i for i, _, _ in INDUSTRIES if i not in by_id] + [i for i in by_id if i not in {x for x, _, _ in INDUSTRIES}]
    if missing:
        raise SystemExit(f'build-home.py INDUSTRIES and content/variants/ disagree: {missing}')
    w, h = INDUSTRY_THUMB
    tiles = ''
    for vid, en, he in INDUSTRIES:
        v, img = by_id[vid], f'images/home2/industries/{vid}.webp'
        if not os.path.exists(sc.rel(img)):
            raise SystemExit(f'{img} is missing: run python3 tools/make_industry_thumbs.py')
        line = T(H.escape(first_sentence(v['intro']['statement_en'])), H.escape(first_sentence(v['intro']['statement_he'])))
        tiles += (f'<a class="ind reveal" href="/{v["path"]}/"><span class="ph"><img src="/{img}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async"></span>'
                  f'<h3 class="serif">{T(H.escape(en), H.escape(he))}</h3><p>{line}</p></a>')
    return ('\n\n<section class="section wrap" id="industries">\n'
            f'  <div class="head reveal"><div class="lead"><p class="eyebrow">{T("Who I work with", "עם מי אני עובדת")}</p>'
            f'<h2 class="serif">{T("Art for every kind of space", "אמנות לכל סוג של חלל")}</h2></div></div>\n'
            f'  <div class="ind-grid">{tiles}</div>\n</section>')


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


def num(x):
    """A room's value as the page writes it: numbers at four decimals (0.0001 of a room is under a pixel)."""
    if isinstance(x, list):
        return [num(y) for y in x]
    return round(x, 4) if isinstance(x, float) else x


def pct(x):
    return f'{round(x * 100, 2):g}%'


def room_region(name, inner, rooms, drop=False):
    """A room region: the homepage's bytes, unless the variant replaces that slot's room. rooms_js then
    sets window.THEODORA_ROOMS (each room with its slot), room_cap_N is the room's caption, and
    room_fig_N the homepage's static figure with the room's focal point, after image, alt and caption.
    With drop (rooms_rest "drop", the default beside rooms), the slots past the variant's last room are
    dropped instead of showing the homepage's: no figure, an empty caption, and
    window.THEODORA_ROOMS_ONLY tells js/home-opening.js to end the opening after the last room."""
    if name == 'rooms_js':
        if not rooms:
            return inner
        data = [{'slot': i, **{k: num(r[k]) for k in ROOM_KEYS + ('seed',) if k in r}} for i, r in enumerate(rooms)]
        only = ' window.THEODORA_ROOMS_ONLY = true;' if drop else ''
        return inner + '\n<script>window.THEODORA_ROOMS = ' + json.dumps(data, separators=(',', ':')).replace('</', '<\\/') + ';' + only + '</script>'
    slot = int(name.rsplit('_', 1)[1])
    if slot >= len(rooms):
        return '' if (rooms and drop) else inner
    r = rooms[slot]
    cap = T(H.escape(r['cap_en']), H.escape(r['cap_he']))
    if name.startswith('room_cap_'):
        return cap
    for pattern, new in ((r'style="--fx:[^;"]*;--fy:[^;"]*"', f'style="--fx:{pct(r["fx"])};--fy:{pct(r["fy"])}"'),
                         (r'<img src="[^"]*" alt="[^"]*"', f'<img src="/images/home2/{H.escape(r["a"], quote=True)}" alt="{H.escape(r["alt_en"], quote=True)}"'),
                         (r'<figcaption>.*?</figcaption>', f'<figcaption>{cap}</figcaption>')):
        inner, n = re.subn(pattern, lambda _m: new, inner, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f'templates/home.html: the static figure in {name} no longer matches {pattern}')
    return inner


def value_strip(v):
    """A variant's value strip: three columns, each a label and one line, in both languages."""
    items = ''.join(
        f'<div class="vs-item reveal"><h3 class="serif">{T(H.escape(i["label_en"]), H.escape(i["label_he"]))}</h3>'
        f'<p class="body">{T(H.escape(i["line_en"]), H.escape(i["line_he"]))}</p></div>'
        for i in v['value_strip'])
    return f'\n\n<section class="value-strip wrap" id="value">{items}</section>'


def fill_regions(body, v):
    """The marked regions: the template's own text for the homepage (the markers go, the bytes
    between them stay), the variant's copy otherwise. Every region must appear exactly once, and
    room_fig_N and room_cap_N must hold slot N of PAIRS in js/home-opening.js. A variant-only block
    (BLOCKS) is empty in the template and rendered whole for a variant."""
    seen = collections.Counter()
    rooms = (v or {}).get('rooms') or []
    drop = bool(rooms) and (v or {}).get('rooms_rest', 'drop') == 'drop'
    inside = {m.group(1): m.group(2) for m in MARK.finditer(body)}
    for i, (key, _, after) in enumerate(HOME_ROOMS):
        if f'data-cap="{key}"><!--variant:room_cap_{i}-->' not in body or f'src="/images/home2/{after}"' not in inside.get(f'room_fig_{i}', ''):
            raise SystemExit(f'templates/home.html: room_fig_{i} and room_cap_{i} must hold slot {i} of PAIRS in js/home-opening.js ({key}, {after})')

    def fill(m):
        name, inner = m.group(1), m.group(2)
        seen[name] += 1
        if name in ROOM_REGIONS:
            return room_region(name, inner, rooms, drop)
        if name in DROPS:
            return inner if v is None else ''
        if name in BLOCKS:
            assert inner == '', f'the {name} marker in the template must be empty (the homepage has no {name})'
            if v is None:
                return ''
            if not v.get(name):
                raise SystemExit(f"content/variants/{v['id']}.json: {name} is missing")
            return value_strip(v)
        pair = region_copy(v, name) if v is not None and name in REGIONS else None
        if pair is None:
            return inner
        en, he = pair
        return T(en, he) if name in HTML_REGIONS else T(H.escape(en), H.escape(he))

    body = MARK.sub(fill, body)
    assert set(seen) == set(REGIONS) | ROOM_REGIONS | BLOCKS | DROPS and all(n == 1 for n in seen.values()), f'variant regions in the template: {dict(seen)}'
    assert '<!--variant:' not in body and '<!--/variant:' not in body, 'a variant marker was left in the page'
    return body


def render_home(pages, posts, faq, v=None, variants=()):
    """The homepage, or with v (a loaded variant) the same page with the variant's copy at /<path>/."""
    tmpl = open(TEMPLATE, encoding='utf-8').read()
    projects = [pages['projects/' + s] for s in PROJECT_ORDER]
    subject = v['mail_subject'] if v else ''
    questions = v['faq'] if v else faq
    fills = {
        'NAV': sc.nav(home=True),
        'INDUSTRIES': '' if v else industries(variants),
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
    url = f"{SITE}/{v['path']}/" if v else SITE + '/'  # a variant is its own canonical, and indexable (Ron, 2026-09-28)
    # a variant may bring its own preview image (head.og_image, 1200 by 630) and its own first room
    og_image, og_alt = (SITE + meta['og_image'], meta['og_image_alt']) if meta.get('og_image') else (OG_IMAGE, OG_IMAGE_ALT)
    rooms = (v or {}).get('rooms')
    head = sc.head(meta['title'], meta['description'], url, og_title=meta['og_title'], og_desc=meta['og_description'],
                   og_image=og_image, og_card_dims=True, og_image_alt=og_alt, lang='en', ld=[sc.faq_schema(questions)],
                   extra=preload(rooms[0]['b'], rooms[0]['a']) if rooms else PRELOAD)
    return head + body


def section(page, sid):
    m = re.search(r'<section\b[^>]*\bid="' + sid + r'"[^>]*>.*?</section>', page, re.S)
    return m.group(0) if m else None


def page_problems(out, name, home=None):
    """What stops a page from being written. With home (the rendered homepage), out is a variant:
    it must also be indexable (since 2026-09-28) and carry the shared sections exactly as the homepage does."""
    problems = []
    if re.search('[\\u2013\\u2014]', re.sub(r'<script.*?</script>', '', out, flags=re.S)):
        problems.append(f'em or en dash in {name}')
    en, he = out.count('data-l="en"'), out.count('data-l="he"')
    if en != he:
        problems.append(f'twins differ in {name}: {en} en, {he} he')
    for anchor in ANCHORS:
        if f'id="{anchor}"' not in out and not (home is not None and anchor in VARIANT_ABSENT):
            problems.append(f'anchor #{anchor} missing')
    if home is not None:
        for sid in VARIANT_ABSENT:
            if f'id="{sid}"' in out or f'href="#{sid}"' in out:
                problems.append(f'{name} still carries #{sid} or a link to it (a homepage-only section)')
        if 'name="robots"' in out:
            problems.append(f'{name} carries a robots meta tag; buyer variants are indexable (Ron, 2026-09-28)')
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
    out = render_home(pages, posts, faq, variants=load_variants(faq))
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
