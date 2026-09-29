#!/usr/bin/env python3
"""Mechanical gate for the buyer variants of the homepage, content/variants/<id>.json.

    python3 tools/check_variants.py                     every content/variants/*.json
    python3 tools/check_variants.py /any/dir/<id>.json  these files, wherever they live (drafts too)

Prints OK or the failures for each file, and warnings that do not fail it. Exit 1 on any
failure; no variants at all is not a failure. python3 build.py runs it before build-home.py.
The fields and limits are documented in content/VARIANT-SPEC.md. The checks:

  a  the JSON parses; known keys only, none starting with "_"; id is the file name and a slug;
     path is one or two slug segments, the last one the id, no leading or trailing slash
  b  the path's first segment is no site folder and no growth page; the path is unique among
     the variants (the ones checked and content/variants); an existing /<path>/ holds only
     a variant's index.html
  c  approved reads "Ron YYYY-MM-DD" or "Stav YYYY-MM-DD"
  d  every required field is present, every _en has its _he twin and the reverse
  e  every string is trimmed and single spaced, with no en or em dash, no phone number, no
     "contact form", no slot, comment or placeholder; English carries no Hebrew letters, Hebrew
     carries them and differs from its English twin
  f  no hype word (tools/check_pages.py HYPE); a $ or % figure only beside the word "industry"
  g  lengths, per field (content/VARIANT-SPEC.md)
  h  HTML only in what_i_do.p1 and p2 (a, em, strong); links go to existing pages or homepage
     anchors, the same set in both languages; no mailto, no link to the variant itself (links to the other
     buyer pages are welcome since 2026-09-29, Ron's SEO brief P1.5)
  i  five to seven questions after resolving {"home": "<q_en>"}; each under 110 characters and
     ending in "?", English answers of 40 to 90 words, Hebrew ones at least 0.6 of that, no repeats
  j  advisory_rows (optional): three to eight different content/pages paths or hubs, all built
  k  warning only: "we", "our" or "us" where Stav speaks for herself (questions and the subject exempt)
  l  rooms (optional): one to four rooms for the opening, entry i in slot i (0 is the first fold);
     b and a are two .webp files in images/home2/variants/<id>/, in the repo, each under 250 KB,
     w by h pixels, about 3:2 (portrait phones draw every room whole in a 3:2 frame), and no
     image of the homepage's rooms or of another slot; rect [u0, v0, u1, v1] inside 0..1 with
     u0 < u1 and v0 < v1; fx and fy in 0..1; from "left" or "right"; seed a number when given;
     cap_en and cap_he start "Proposal. " and "הצעה. "; the alt and caption twins take e to h;
     rooms_rest (optional, only beside rooms): "drop" (the default) ends the opening after the last
     room, "home" keeps the homepage's rooms in the slots after it
  m  head.og_image with head.og_image_alt (optional): the variant's own link preview, a JPEG in
     images/home2/variants/<id>/, 1200 by 630, under 300 KB
  n  value_strip: exactly three items {label_en, label_he, line_en, line_he}, plain text, labels at most
     40 characters and lines at most 170 (the English), no label or line repeated
  o  indexing (2026-09-28): guide.who (the direct "who does this" answer, the long section's first
     paragraph, 80 to 260 characters, naming Stav Theodor); service {service_type, audience, area_served} for the Service schema, area_served
     from New York City and New Jersey (never Tel Aviv, 2026-09-29); guide {eyebrow, h2, body} with a body of 600 to 900
     English words (p, h3, ul, ol, li, a, em, strong; links as in h, the same set in both languages)
"""
import ast
import datetime
import glob
import hashlib
import json
import math
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARIANTS_DIR = os.path.join(ROOT, 'content', 'variants')


def constant(script, name):
    """A module-level constant of another gate, read without running it: check_site.py and
    check_pages.py run their checks as soon as they are imported."""
    path = os.path.join(ROOT, 'tools', script)
    for node in ast.parse(open(path, encoding='utf-8').read(), path).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            value = node.value
            if isinstance(value, ast.Call) and value.args:  # PHONE = re.compile(r'...')
                value = value.args[0]
            return ast.literal_eval(value)
    raise SystemExit(f'check_variants: no {name} in tools/{script}')


HYPE = constant('check_pages.py', 'HYPE')
PHONE = re.compile(constant('check_site.py', 'PHONE'))
SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
APPROVED = re.compile(r'^(Ron|Stav) (\d{4}-\d{2}-\d{2})$')
HEBREW = re.compile('[\\u0590-\\u05ff]')
DASH = re.compile('[\\u2013\\u2014]')
MONEY = re.compile(r'\$\s?\d|\d+\s?%')
TAG = re.compile(r'<(/?)([A-Za-z0-9]+)([^>]*)>')
ENTITY = re.compile(r'&(#\d+|#x[0-9a-fA-F]+|[A-Za-z]+);')
WE = re.compile(r'\b(?:[Ww]e|[Oo]ur|us)\b')
BANNED = [('contact form', True), ('{{', False), ('<!--', False), ('PLACEHOLDER', False), ('TODO', False), ('lorem', True)]

# object: (required keys, optional keys); services and faq hold lists of these objects
SCHEMA = {
    '': ({'id', 'path', 'approved', 'head', 'hero', 'intro', 'service', 'services', 'value_strip', 'what_i_do', 'guide', 'faq', 'cta_en', 'cta_he', 'mail_subject'},
         {'advisory', 'advisory_rows', 'rooms', 'rooms_rest'}),
    'head': ({'title', 'description', 'og_title', 'og_description'}, {'og_image', 'og_image_alt'}),
    'hero': ({'l1_en', 'l1_he', 'l2_en', 'l2_he'}, set()),
    'intro': ({'h1_en', 'h1_he', 'line_en', 'line_he', 'statement_en', 'statement_he'}, {'eyebrow_en', 'eyebrow_he'}),
    'service': ({'service_type', 'audience', 'area_served'}, set()),
    'guide': ({'eyebrow_en', 'eyebrow_he', 'h2_en', 'h2_he', 'who_en', 'who_he', 'body_en', 'body_he'}, set()),
    'services': ({'desc_en', 'desc_he'}, set()),
    'value_strip': ({'label_en', 'label_he', 'line_en', 'line_he'}, set()),
    'what_i_do': ({'h2_en', 'h2_he', 'p1_en', 'p1_he', 'p2_en', 'p2_he'}, {'eyebrow_en', 'eyebrow_he'}),
    'advisory': (set(), {'h2_en', 'h2_he', 'sub_en', 'sub_he'}),
    'faq': ({'q_en', 'a_en', 'q_he', 'a_he'}, set()),
    'rooms': ({'b', 'a', 'w', 'h', 'rect', 'fx', 'fy', 'from', 'cap_en', 'cap_he', 'alt_en', 'alt_he'}, {'seed'}),
}
OBJECTS = {'head', 'hero', 'intro', 'what_i_do', 'advisory', 'service', 'guide'}
LISTS = {'services', 'value_strip', 'faq', 'advisory_rows', 'rooms', 'area_served'}
NUMBERS = {'w', 'h', 'rect', 'fx', 'fy', 'seed'}  # the rooms' fields that are not strings (checked under l)
HTML_FIELDS = {'what_i_do.p1_en', 'what_i_do.p1_he', 'what_i_do.p2_en', 'what_i_do.p2_he'}
GUIDE_FIELDS = {'guide.body_en', 'guide.body_he'}  # the long section: a reading column's tags too
GUIDE_TAGS = ('a', 'em', 'strong', 'p', 'h3', 'ul', 'ol', 'li')
AREAS = ('New York City', 'New Jersey')  # never Tel Aviv in an areaServed (Ron's SEO brief, 2026-09-29)
# (field, min, max) in characters; the minimum and maximum read the English, the hero lines both languages
CHAR_LIMITS = [
    ('head.title', 30, 70), ('head.description', 70, 165), ('head.og_title', 1, 70), ('head.og_description', 1, 160),
    ('head.og_image_alt', 1, 160),
    ('hero.l1_en', 1, 18), ('hero.l1_he', 1, 18), ('hero.l2_en', 1, 18), ('hero.l2_he', 1, 18),
    ('intro.h1_en', 40, 110), ('intro.line_en', 1, 60), ('intro.eyebrow_en', 1, 24), ('intro.statement_en', 60, 160),
    ('what_i_do.eyebrow_en', 1, 24), ('what_i_do.h2_en', 1, 120), ('advisory.h2_en', 1, 90), ('advisory.sub_en', 1, 200),
    ('cta_en', 40, 140), ('mail_subject', 8, 60),
    ('guide.who_en', 80, 260), ('service.service_type', 10, 90), ('service.audience', 5, 90),
    ('guide.eyebrow_en', 1, 24), ('guide.h2_en', 1, 120),
]
WORD_LIMITS = [('what_i_do.p1_en', 40, 160), ('what_i_do.p2_en', 40, 160), ('guide.body_en', 600, 900)]
SERVICE_DESC_MAX = 90
VALUE_STRIP_COUNT = 3
VALUE_LABEL_MAX, VALUE_LINE_MAX = 40, 170
FAQ_COUNT = (5, 7)
FAQ_ANSWER_WORDS = (40, 90)
QUESTION_MAX = 110
HEBREW_SHARE = 0.6
ROWS_COUNT = (3, 8)
HUBS = ('/advisory/', '/projects/')
STUBS = ('2', 'about', 'our-team', 'our-team-1', 'questions', 'designers')  # /contact/ is a real page since 2026-09-29; /designers/ forwards to /for-designers/
RESERVED = {'2', 'about', 'advisory', 'art-curator-new-jersey', 'art-curator-new-york', 'contact', 'content', 'css', 'designers', 'fonts',
            'for-advisors', 'for-brokers', 'for-designers', 'guide', 'images', 'js', 'museum', 'our-team', 'our-team-1',
            'projects', 'questions', 'radar', 'templates', 'tools', 'videos'}
# l and m: the opening's rooms and the link preview. HOME_ROOMS is PAIRS in js/home-opening.js, [(before, after)] in
# slot order, paths under images/home2/; a variant's images live in images/home2/variants/<id>/.
HOME2 = os.path.join(ROOT, 'images', 'home2')
HOME_ROOMS = re.findall(r"cap: '\w+',[^\n]*?land: \{ b: '([^']+)', a: '([^']+)'",
                        open(os.path.join(ROOT, 'js', 'home-opening.js'), encoding='utf-8').read())
if not HOME_ROOMS:
    raise SystemExit('check_variants: no rooms read from PAIRS in js/home-opening.js (did its format change?)')
FILE_NAME = r'[a-z0-9]+(?:[_-][a-z0-9]+)*'
ROOM_MAX_BYTES = 250000
ROOM_ASPECT = (1.455, 1.545)  # 3:2 within 3 percent: FIT_ASPECT in js/home-opening.js draws portrait rooms at 3:2
CAP_PREFIX = {'cap_en': 'Proposal. ', 'cap_he': 'הצעה. '}
CAP_MAX, ALT_MAX = 120, 160  # English characters; the homepage's longest caption is 106
OG_SIZE = (1200, 630)
OG_MAX_BYTES = 300000

PAGES = {}
for _f in sorted(glob.glob(os.path.join(ROOT, 'content', 'pages', '*.json'))):
    _p = json.load(open(_f, encoding='utf-8'))
    PAGES[_p['path'].strip('/')] = _p
RESERVED |= {p.split('/')[0] for p in PAGES}
HOME_FAQ = {q['q_en']: q for q in json.load(open(os.path.join(ROOT, 'content', 'faq.json'), encoding='utf-8'))}
HOME = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read() if os.path.exists(os.path.join(ROOT, 'index.html')) else ''


def words(s):
    return len(re.sub(r'<[^>]+>', ' ', s).split())


def load(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError) as e:
        return e


def get(v, field):
    """v['intro']['h1_en'] for 'intro.h1_en', None when any part is absent."""
    node = v
    for part in field.split('.'):
        node = node.get(part) if isinstance(node, dict) else None
    return node


def strings(v):
    """(label, text) for every string the variant writes onto the page, its own FAQ included."""
    out = []
    for key in ('head', 'hero', 'intro', 'what_i_do', 'advisory', 'service', 'guide'):
        for k, s in (v.get(key) or {}).items():
            if (key, k) != ('head', 'og_image'):  # a path, checked under m
                out.append((f'{key}.{k}', s))
    for name in ('services', 'value_strip'):
        for i, item in enumerate(v.get(name) or []):
            for k, s in (item if isinstance(item, dict) else {}).items():
                out.append((f'{name}[{i}].{k}', s))
    for i, item in enumerate(v['rooms'] if isinstance(v.get('rooms'), list) else []):
        for k, s in (item if isinstance(item, dict) else {}).items():
            if k in ('cap_en', 'cap_he', 'alt_en', 'alt_he'):
                out.append((f'rooms[{i}].{k}', s))
    for i, item in enumerate(v.get('faq') or []):
        if isinstance(item, dict) and 'home' not in item:
            for k, s in item.items():
                out.append((f'faq[{i}].{k}', s))
    for k in ('cta_en', 'cta_he', 'mail_subject'):
        if k in v:
            out.append((k, v[k]))
    return out


def language(label):
    if label.endswith('_he'):
        return 'he'
    if label.endswith('_en') or label.startswith(('head.', 'service.')) or label == 'mail_subject':
        return 'en'
    return None


def twin(v, label):
    """The English twin of a Hebrew field: 'faq[2].a_he' -> the value of faq[2].a_en."""
    m = re.match(r'^(\w+)(?:\[(\d+)\])?(?:\.(\w+))?$', label)
    obj, idx, key = m.group(1), m.group(2), m.group(3)
    if key is None:
        return v.get(obj[:-3] + '_en')
    node = v.get(obj)
    if idx is not None:
        node = node[int(idx)] if isinstance(node, list) and int(idx) < len(node) else None
    return node.get(key[:-3] + '_en') if isinstance(node, dict) else None


def link_problems(label, href, variant_paths):
    if href.startswith('mailto:'):
        return [f'{label}: no mailto links (the footer carries the mail link and its subject)']
    if href.startswith('#'):
        return [] if f'id="{href[1:]}"' in HOME else [f'{label}: {href} is not an id on the homepage']
    if not href.startswith('/') or href.startswith('//'):
        return [f'{label}: {href} must be root-relative (/path/) or a homepage #anchor']
    rel, _, frag = href[1:].partition('#')
    if '?' in rel or (rel and not rel.endswith('/')):
        return [f'{label}: {href} must be a page address ending in a slash, like /advisory/']
    if rel.split('/')[0] in STUBS:
        return [f'{label}: {href} is a redirect stub; link the page it forwards to']
    if any(rel.strip('/') == p or rel.startswith(p + '/') for p in variant_paths):
        return [f'{label}: {href} is this buyer page itself']
    target = os.path.join(ROOT, rel, 'index.html')
    if not os.path.exists(target):
        return [f'{label}: {href} is not a page on the site']
    page = open(target, encoding='utf-8').read()
    if 'name="robots" content="noindex"' in page:
        return [f'{label}: {href} is a noindex page']
    if frag and f'id="{frag}"' not in page:
        return [f'{label}: {href} has no id="{frag}" on that page']
    return []


def html_problems(label, s, variant_paths, allowed=('a', 'em', 'strong')):
    """what_i_do.p1 and p2: a, em and strong only (guide.body: GUIDE_TAGS), balanced, links checked. Returns (problems, hrefs)."""
    problems, hrefs, depth = [], [], {}
    for close, name, attrs in TAG.findall(s):
        name = name.lower()
        if name not in allowed:
            problems.append(f'{label}: <{name}> is not allowed ({", ".join(allowed)} only)')
            continue
        depth[name] = depth.get(name, 0) + (-1 if close else 1)
        if close or name != 'a':
            if attrs.strip():
                problems.append(f'{label}: <{close}{name}{attrs}> takes no attributes')
            continue
        m = re.fullmatch(r'\s+href="([^"]*)"\s*', attrs)
        if not m:
            problems.append(f'{label}: <a{attrs}> must carry exactly one href="..." and nothing else')
            continue
        hrefs.append(m.group(1))
        problems += link_problems(label, m.group(1), variant_paths)
    if any(depth.values()):
        problems.append(f'{label}: unbalanced tags {sorted(k for k, n in depth.items() if n)}')
    if re.search(r'[<>]', TAG.sub('', s)):
        problems.append(f'{label}: a stray < or > outside a tag')
    return problems, hrefs


SOF = {0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf}  # the JPEG frame headers


def image_size(path):
    """('webp' or 'jpeg', width, height) read from the file's header, None for anything else."""
    with open(path, 'rb') as f:
        head = f.read(30)
        if head[:4] == b'RIFF' and head[8:12] == b'WEBP' and len(head) == 30:
            chunk = head[12:16]
            if chunk == b'VP8 ' and head[23:26] == b'\x9d\x01\x2a':  # lossy
                w, h = struct.unpack('<HH', head[26:30])
                return 'webp', w & 0x3fff, h & 0x3fff
            if chunk == b'VP8L' and head[20] == 0x2f:  # lossless
                bits = int.from_bytes(head[21:25], 'little')
                return 'webp', (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
            if chunk == b'VP8X':  # extended: the canvas size
                return 'webp', int.from_bytes(head[24:27], 'little') + 1, int.from_bytes(head[27:30], 'little') + 1
            return None
        if head[:2] != b'\xff\xd8':
            return None
        f.seek(2)
        while True:
            marker = f.read(2)
            while len(marker) == 2 and marker[1] == 0xff:  # fill bytes before a marker
                marker = marker[1:] + f.read(1)
            if len(marker) < 2 or marker[0] != 0xff or marker[1] in (0xd9, 0xda):  # broken, or no frame header before the scan
                return None
            if marker[1] == 0x01 or 0xd0 <= marker[1] <= 0xd7:  # markers without a length
                continue
            seg = f.read(2)
            if len(seg) < 2:
                return None
            if marker[1] in SOF:
                data = f.read(5)  # precision, height, width
                return ('jpeg',) + struct.unpack('>HH', data[3:5] + data[1:3]) if len(data) == 5 else None
            f.seek(struct.unpack('>H', seg)[0] - 2, 1)


def digest(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def number(x, lo=None, hi=None):
    """A JSON number (not true or false), finite, and from lo to hi when they are given."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and (lo is None or lo <= x <= hi)


def room_problems(rooms, vid):
    """l: the rooms a variant puts in the opening, entry i in slot i (the keys and the twins are checked under a and d)."""
    if not isinstance(rooms, list) or not 1 <= len(rooms) <= len(HOME_ROOMS):
        return [f'rooms: a list of 1 to {len(HOME_ROOMS)} rooms, entry i replacing slot i of the opening (0 is the first fold)']
    fails, used = [], {}
    home = {digest(os.path.join(HOME2, n)) for pair in HOME_ROOMS for n in pair if os.path.isfile(os.path.join(HOME2, n))}
    for i, r in enumerate(rooms):
        where = f'rooms[{i}]'
        if not isinstance(r, dict):
            continue
        w, h = r.get('w'), r.get('h')
        size_ok = all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in (w, h))
        if 'w' in r and 'h' in r:
            if not size_ok:
                fails.append(f'{where}: w and h are the images\' width and height in pixels, whole numbers')
            elif not ROOM_ASPECT[0] <= w / h <= ROOM_ASPECT[1]:
                fails.append(f'{where}: {w} by {h} is not 3:2 (w / h is {w / h:.3f}); portrait phones draw every room whole in a 3:2 frame')
        for k in ('b', 'a'):
            name, label = r.get(k), f'{where}.{k}'
            if not isinstance(name, str) or not name:
                continue
            if not re.fullmatch(rf'variants/{re.escape(vid)}/{FILE_NAME}\.webp', name):
                fails.append(f'{label} "{name}": a .webp in the variant\'s own folder, variants/{vid}/<name>.webp (under images/home2/)')
                continue
            path = os.path.join(HOME2, name)
            if not os.path.isfile(path):
                fails.append(f'{label}: images/home2/{name} is not in the repo')
                continue
            n = os.path.getsize(path)
            if n >= ROOM_MAX_BYTES:
                fails.append(f'{label}: images/home2/{name} is {n} bytes, keep each image under 250 KB')
            size = image_size(path)
            if not size or size[0] != 'webp':
                fails.append(f'{label}: images/home2/{name} is not a WebP image')
            elif size_ok and size[1:] != (w, h):
                fails.append(f'{label}: images/home2/{name} is {size[1]} by {size[2]} pixels, w and h say {w} by {h}')
            d = digest(path)
            if d in home:
                fails.append(f'{label}: images/home2/{name} is an image of the homepage\'s own rooms')
            if d in used:
                fails.append(f'{label}: images/home2/{name} is the same image as {used[d]}')
            used.setdefault(d, label)
        rect = r.get('rect')
        if 'rect' in r and not (isinstance(rect, list) and len(rect) == 4 and all(number(x, 0, 1) for x in rect)
                                and rect[0] < rect[2] and rect[1] < rect[3]):
            fails.append(f'{where}.rect: the artwork in the after image, [u0, v0, u1, v1] inside 0..1 with u0 < u1 and v0 < v1')
        for k in ('fx', 'fy'):
            if k in r and not number(r[k], 0, 1):
                fails.append(f'{where}.{k}: the focal point, a number from 0 to 1')
        if 'from' in r and r['from'] not in ('left', 'right'):
            fails.append(f'{where}.from: "left" or "right", the side of the artwork where the brush lands')
        if 'seed' in r and not number(r['seed']):
            fails.append(f'{where}.seed: a number; leave it out to keep the slot\'s own')
        for k, prefix in CAP_PREFIX.items():
            s = r.get(k)
            if isinstance(s, str) and s and not (s.startswith(prefix) and len(s) > len(prefix)):
                fails.append(f'{where}.{k}: starts "{prefix}" and then describes the room, like the homepage\'s captions')
        for k, most in (('cap_en', CAP_MAX), ('alt_en', ALT_MAX)):
            s = r.get(k)
            if isinstance(s, str) and len(s) > most:
                fails.append(f'{where}.{k}: {len(s)} characters, at most {most}')
    return fails


def og_problems(head, vid):
    """m: the variant's own link preview, in place of og-home.jpg."""
    img, alt = head.get('og_image'), head.get('og_image_alt')
    if not (isinstance(img, str) and img and isinstance(alt, str) and alt):
        return ['head.og_image and head.og_image_alt come together: the preview image and what it shows']
    if not re.fullmatch(rf'/images/home2/variants/{re.escape(vid)}/{FILE_NAME}\.jpg', img):
        return [f'head.og_image "{img}": a .jpg in the variant\'s own folder, /images/home2/variants/{vid}/<name>.jpg']
    path = os.path.join(ROOT, img[1:])
    if not os.path.isfile(path):
        return [f'head.og_image: {img[1:]} is not in the repo']
    fails, size, n = [], image_size(path), os.path.getsize(path)
    if not size or size[0] != 'jpeg':
        fails.append(f'head.og_image: {img[1:]} is not a JPEG')
    elif size[1:] != OG_SIZE:
        fails.append(f'head.og_image: {img[1:]} is {size[1]} by {size[2]} pixels, the preview card is 1200 by 630')
    if n >= OG_MAX_BYTES:
        fails.append(f'head.og_image: {img[1:]} is {n} bytes, keep it under 300 KB')
    return fails


def check(path, v, peers):
    fails, warns = [], []
    stem = os.path.splitext(os.path.basename(path))[0]
    if isinstance(v, Exception):
        return [f'the JSON does not parse: {v}'], warns
    if not isinstance(v, dict):
        return ['the file must hold one JSON object'], warns

    # a: keys, id, path
    def keys(obj, name, where):
        if not isinstance(obj, dict):
            fails.append(f'{where} must be an object')
            return
        required, optional = SCHEMA[name]
        for k in obj:
            if k.startswith('_'):
                fails.append(f'{where}{k}: editor keys (starting with _) are not allowed here')
            elif name == 'faq' and k == 'home':
                continue
            elif k not in required | optional:
                fails.append(f'{where}{k}: unknown key')
        if name == 'faq' and 'home' in obj:
            if set(obj) != {'home'} or not isinstance(obj['home'], str):
                fails.append(f'{where[:-1]}: a homepage question is {{"home": "<its q_en>"}} and nothing else')
            return
        for k in sorted(required - set(obj)):
            fails.append(f'{where}{k}: missing')
        for k, s in obj.items():
            if k in (required | optional) - OBJECTS - LISTS - (NUMBERS if name == 'rooms' else set()) and not (isinstance(s, str) and s):
                fails.append(f'{where}{k}: must be a non-empty string')
    keys(v, '', '')
    for name in sorted(OBJECTS):
        if name in v:
            keys(v[name], name, f'{name}.')
    for name in ('services', 'value_strip', 'faq', 'rooms'):
        items = v.get(name)
        if name in v and not isinstance(items, list):
            fails.append(f'{name} must be a list')
            continue
        for i, item in enumerate(items or []):
            keys(item, name, f'{name}[{i}].')
    if isinstance(v.get('services'), list) and len(v['services']) != 4:
        fails.append(f'services: exactly 4 entries, one per service column (found {len(v["services"])})')
    if isinstance(v.get('value_strip'), list) and len(v['value_strip']) != VALUE_STRIP_COUNT:
        fails.append(f'value_strip: exactly {VALUE_STRIP_COUNT} items, one per column (found {len(v["value_strip"])})')
    v = dict(v)  # a normalized copy: what is missing or of the wrong type is reported above, empty below
    for k in OBJECTS:
        v[k] = v[k] if isinstance(v.get(k), dict) else {}
    for k in ('services', 'value_strip', 'faq'):
        v[k] = v[k] if isinstance(v.get(k), list) else []
    for k in ('id', 'path', 'approved', 'cta_en', 'cta_he', 'mail_subject'):
        v[k] = v[k] if isinstance(v.get(k), str) else ''
    vid, vpath = v.get('id') or '', v.get('path') or ''
    if vid != stem:
        fails.append(f'id "{vid}" must equal the file name ({stem}.json)')
    if not SLUG.match(vid):
        fails.append(f'id "{vid}" is not a slug (lowercase letters, digits, single hyphens)')
    segs = vpath.split('/')
    path_ok = vpath == vpath.strip('/') and 1 <= len(segs) <= 2 and all(SLUG.match(s) for s in segs)
    if not path_ok:
        fails.append(f'path "{vpath}": one or two slug segments, no leading or trailing slash')
    elif segs[-1] != vid:
        fails.append(f'path "{vpath}": its last segment must be the id ({vid})')

    # b: reserved, unique, the folder
    if segs[0] in RESERVED:
        fails.append(f'path "{vpath}": /{segs[0]}/ belongs to the site (a folder or a growth page)')
    subject = v['mail_subject'].strip().lower()
    for other_path, o in peers:
        where = os.path.relpath(other_path, ROOT) if other_path.startswith(ROOT + os.sep) else other_path
        op = o.get('path') if isinstance(o.get('path'), str) else ''
        if op == vpath and vpath:
            fails.append(f'path "{vpath}" is also used by {where}')
        elif vpath and op and (op.startswith(vpath + '/') or vpath.startswith(op + '/')):
            fails.append(f'path "{vpath}" nests with {where} ("{op}")')
        if o.get('id') == vid and vid:
            fails.append(f'id "{vid}" is also used by {where}')
        if subject and isinstance(o.get('mail_subject'), str) and o['mail_subject'].strip().lower() == subject:
            fails.append(f'mail_subject is also used by {where}; every variant needs its own')
    folder = os.path.join(ROOT, vpath)
    if path_ok and os.path.isdir(folder):
        extra = sorted(set(os.listdir(folder)) - {'index.html'})
        if extra:
            fails.append(f'/{vpath}/ already holds {extra}: a variant folder holds only its index.html')
        index = os.path.join(folder, 'index.html')
        if os.path.exists(index) and 'data-subject="' not in open(index, encoding='utf-8').read():
            fails.append(f'/{vpath}/index.html is a page that is not a variant; choose another path')

    # c: approval
    m = APPROVED.match(v.get('approved') or '')
    if not m:
        fails.append('approved must read "Ron YYYY-MM-DD" or "Stav YYYY-MM-DD" (who approved the copy, and when)')
    else:
        try:
            datetime.date.fromisoformat(m.group(2))
        except ValueError:
            fails.append(f'approved: {m.group(2)} is not a date')

    # d: twins (the required keys were checked with the schema)
    def twins(obj, where):
        for k in obj:
            if k.endswith('_en') and k[:-3] + '_he' not in obj:
                fails.append(f'{where}{k} has no Hebrew twin {k[:-3]}_he')
            if k.endswith('_he') and k[:-3] + '_en' not in obj:
                fails.append(f'{where}{k} has no English twin {k[:-3]}_en')
    twins(v, '')
    for name in ('hero', 'intro', 'what_i_do', 'advisory', 'guide'):
        twins(v[name] if isinstance(v[name], dict) else {}, f'{name}.')
    for name in ('services', 'value_strip', 'faq', 'rooms'):
        for i, item in enumerate(v[name] if isinstance(v.get(name), list) else []):
            if isinstance(item, dict):
                twins(item, f'{name}[{i}].')

    variant_paths = [vpath]  # the page itself; the other buyer pages may be linked since 2026-09-29 (Ron's SEO brief, P1.5)
    hrefs = {}
    for label, s in strings(v):
        if not isinstance(s, str) or not s:
            continue
        lang = language(label)
        # e: the text itself
        if s != s.strip():
            fails.append(f'{label}: leading or trailing space')
        if '  ' in s or re.search(r'[\t\r\n]', s):
            fails.append(f'{label}: double space, tab or line break')
        if DASH.search(s):
            fails.append(f'{label}: an en or em dash (use a comma, colon, period or parentheses)')
        if PHONE.search(s):
            fails.append(f'{label}: looks like a phone number')
        for word, anycase in BANNED:
            if (word in s.lower()) if anycase else (word in s):
                fails.append(f'{label}: contains "{word}"')
        if 'mailto:' in s:
            fails.append(f'{label}: no mailto (the footer carries the mail link and its subject)')
        if lang == 'en' and HEBREW.search(s):
            fails.append(f'{label}: Hebrew letters in an English field')
        if lang == 'he':
            if not HEBREW.search(s):
                fails.append(f'{label}: no Hebrew letters in a Hebrew field')
            elif s == twin(v, label):
                fails.append(f'{label}: identical to its English twin')
        # f: hype and figures
        if lang == 'en':
            low = s.lower()
            for h in HYPE:
                if h in low:
                    fails.append(f'{label}: hype word "{h}"')
            if MONEY.search(s) and 'industry' not in low:
                fails.append(f'{label}: a $ or % figure without the word "industry" (Stav\'s fees are never published)')
        # h: HTML only in the two paragraphs
        if label in HTML_FIELDS | GUIDE_FIELDS:
            problems, found = html_problems(label, s, variant_paths, GUIDE_TAGS if label in GUIDE_FIELDS else ('a', 'em', 'strong'))
            fails.extend(problems)
            hrefs[label] = set(found)
        elif TAG.search(s) or re.search(r'<[A-Za-z!/]', s) or ENTITY.search(s):
            fails.append(f'{label}: HTML or an HTML entity; plain text here (HTML only in what_i_do.p1 and p2), write & and quotes as they are')
        # k: Stav speaks as "I"
        if lang == 'en' and label != 'mail_subject' and not re.search(r'\.q_en$', label):
            found = sorted(set(WE.findall(re.sub(r'<[^>]+>', ' ', s))))
            if found:
                warns.append(f'{label}: {", ".join(found)} (Stav speaks as "I"; fine if it means her and the client)')
    for obj, p in (('what_i_do', 'p1'), ('what_i_do', 'p2'), ('guide', 'body')):
        en, he = hrefs.get(f'{obj}.{p}_en'), hrefs.get(f'{obj}.{p}_he')
        if en is not None and he is not None and en != he:
            fails.append(f'{obj}.{p}: the English and Hebrew link to different pages ({sorted(en)} and {sorted(he)})')
    # o: the who answer names her; the service areas
    who = get(v, 'guide.who_en')
    if isinstance(who, str) and who and 'Stav Theodor' not in who:
        fails.append('guide.who_en: the direct answer names "Stav Theodor"')
    areas = get(v, 'service.area_served')
    if 'service' in v and not (isinstance(areas, list) and areas and all(a in AREAS for a in areas) and len(set(areas)) == len(areas)):
        fails.append(f'service.area_served: a list from {AREAS}, no repeats')

    # g: lengths
    for field, lo, hi in CHAR_LIMITS:
        s = get(v, field)
        if isinstance(s, str) and s and not lo <= len(s) <= hi:
            fails.append(f'{field}: {len(s)} characters, expected {lo} to {hi}' if lo > 1 else f'{field}: {len(s)} characters, at most {hi}')
    for field, lo, hi in WORD_LIMITS:
        s = get(v, field)
        if isinstance(s, str) and s:
            n = words(s)
            if not lo <= n <= hi:
                fails.append(f'{field}: {n} words, expected {lo} to {hi}')
            he = get(v, field[:-3] + '_he')
            if isinstance(he, str) and he and words(he) < HEBREW_SHARE * n:
                fails.append(f'{field[:-3]}_he: {words(he)} words against {n} in English, the translation looks incomplete')
    for i, item in enumerate(v['services']):
        s = item.get('desc_en') if isinstance(item, dict) else None
        if isinstance(s, str) and len(s) > SERVICE_DESC_MAX:
            fails.append(f'services[{i}].desc_en: {len(s)} characters, at most {SERVICE_DESC_MAX}')
    seen_strip = set()
    for i, item in enumerate(v['value_strip']):
        if not isinstance(item, dict):
            continue
        for key, hi in (('label_en', VALUE_LABEL_MAX), ('line_en', VALUE_LINE_MAX)):
            s = item.get(key)
            if isinstance(s, str) and len(s) > hi:
                fails.append(f'value_strip[{i}].{key}: {len(s)} characters, at most {hi}')
        for key in ('label_en', 'label_he', 'line_en', 'line_he'):
            s = item.get(key)
            if isinstance(s, str) and s:
                if s in seen_strip:
                    fails.append(f'value_strip[{i}].{key}: repeats another item of the strip')
                seen_strip.add(s)
    subject = v.get('mail_subject') or ''
    if re.search(r'[\[\](){}<>]', subject):
        fails.append('mail_subject: no brackets (it reads as a natural subject line)')

    # i: the questions, homepage references resolved
    faq, seen = [], set()
    for i, item in enumerate(v['faq']):
        if not isinstance(item, dict):
            fails.append(f'faq[{i}]: must be an object')
        elif 'home' in item:
            if item.get('home') in HOME_FAQ:
                faq.append((f'faq[{i}] (homepage)', HOME_FAQ[item['home']]))
            else:
                fails.append(f'faq[{i}]: {item.get("home")!r} is not a question in content/faq.json')
        else:
            faq.append((f'faq[{i}]', item))
    if not FAQ_COUNT[0] <= len(v['faq']) <= FAQ_COUNT[1]:
        fails.append(f'faq: {len(v["faq"])} questions, expected {FAQ_COUNT[0]} to {FAQ_COUNT[1]}')
    for where, q in faq:
        q_en, q_he, a_en, a_he = (q.get(k) if isinstance(q.get(k), str) else '' for k in ('q_en', 'q_he', 'a_en', 'a_he'))
        if len(q_en) > QUESTION_MAX:
            fails.append(f'{where}.q_en: {len(q_en)} characters, at most {QUESTION_MAX}')
        for k, s in (('q_en', q_en), ('q_he', q_he)):
            if s and not s.endswith('?'):
                fails.append(f'{where}.{k}: a question ends with "?"')
        n = words(a_en)
        if a_en and not FAQ_ANSWER_WORDS[0] <= n <= FAQ_ANSWER_WORDS[1]:
            fails.append(f'{where}.a_en: {n} words, expected {FAQ_ANSWER_WORDS[0]} to {FAQ_ANSWER_WORDS[1]}')
        if a_he and words(a_he) < HEBREW_SHARE * n:
            fails.append(f'{where}.a_he: {words(a_he)} words against {n} in English, the translation looks incomplete')
        for s in (q_en.strip().lower(), q_he.strip()):
            if s and s in seen:
                fails.append(f'{where}: the question "{s}" appears twice')
            seen.add(s)

    # j: advisory rows
    rows = v.get('advisory_rows')
    if rows is not None:
        if not isinstance(rows, list) or not all(isinstance(r, str) and r for r in rows):
            fails.append('advisory_rows: a list of content/pages paths and the hubs /advisory/ and /projects/')
        else:
            norm = ['/' + r.strip('/') + '/' for r in rows]
            if not ROWS_COUNT[0] <= len(rows) <= ROWS_COUNT[1]:
                fails.append(f'advisory_rows: {len(rows)} rows, expected {ROWS_COUNT[0]} to {ROWS_COUNT[1]}')
            if len(set(norm)) != len(norm):
                fails.append('advisory_rows: a row appears twice')
            for r, n in zip(rows, norm):
                if n in HUBS:
                    continue
                if r.strip('/') not in PAGES:
                    fails.append(f'advisory_rows: "{r}" is neither a content/pages path nor /advisory/ or /projects/')
                elif not os.path.exists(os.path.join(ROOT, r.strip('/'), 'index.html')):
                    fails.append(f'advisory_rows: /{r.strip("/")}/ is not built (run python3 build.py)')

    # l: the opening's rooms; m: the link preview
    if 'rooms' in v:
        fails.extend(room_problems(v['rooms'], vid))
    if 'rooms_rest' in v:
        if v['rooms_rest'] not in ('drop', 'home'):
            fails.append(f'rooms_rest: "drop" or "home", not {v["rooms_rest"]!r}')
        if not v.get('rooms'):
            fails.append('rooms_rest: only beside rooms')
    if 'og_image' in v['head'] or 'og_image_alt' in v['head']:
        fails.extend(og_problems(v['head'], vid))
    return fails, warns


def main(args):
    files = args or sorted(glob.glob(os.path.join(VARIANTS_DIR, '*.json')))
    if not files:
        print('check_variants: no variants (content/variants/ is empty or absent), nothing to check')
        return 0
    checked = {os.path.realpath(f): load(f) for f in files}
    repo = {os.path.realpath(f): load(f) for f in sorted(glob.glob(os.path.join(VARIANTS_DIR, '*.json')))}
    failed = 0
    for f in files:
        me = os.path.realpath(f)
        v = checked[me]
        peers = [(g, d) for g, d in checked.items() if g != me and isinstance(d, dict)]
        for g, d in repo.items():  # the repo's variants, except the file itself and the copy a draft replaces
            if g != me and g not in checked and isinstance(d, dict) and not (isinstance(v, dict) and d.get('id') == v.get('id')):
                peers.append((g, d))
        fails, warns = check(f, v, peers)
        name = os.path.relpath(f, ROOT) if me.startswith(ROOT + os.sep) else f
        note = ''.join(f'\n  ! {w}' for w in warns)
        if fails:
            failed += 1
            print(f'{name}: FAIL\n  - ' + '\n  - '.join(fails) + note)
        else:
            print(f'{name}: OK ({len(v["faq"])} questions, {len(warns)} warning(s)){note}')
    print(f'check_variants: {len(files) - failed} of {len(files)} OK')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
