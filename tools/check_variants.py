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
     anchors, the same set in both languages; no mailto, no link to a variant
  i  five to seven questions after resolving {"home": "<q_en>"}; each under 110 characters and
     ending in "?", English answers of 40 to 90 words, Hebrew ones at least 0.6 of that, no repeats
  j  advisory_rows (optional): three to eight different content/pages paths or hubs, all built
  k  warning only: "we", "our" or "us" where Stav speaks for herself (questions and the subject exempt)
"""
import ast
import datetime
import glob
import json
import os
import re
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
    '': ({'id', 'path', 'approved', 'head', 'hero', 'intro', 'services', 'what_i_do', 'faq', 'cta_en', 'cta_he', 'mail_subject'},
         {'advisory', 'advisory_rows'}),
    'head': ({'title', 'description', 'og_title', 'og_description'}, set()),
    'hero': ({'l1_en', 'l1_he', 'l2_en', 'l2_he'}, set()),
    'intro': ({'h1_en', 'h1_he', 'line_en', 'line_he', 'statement_en', 'statement_he'}, {'eyebrow_en', 'eyebrow_he'}),
    'services': ({'desc_en', 'desc_he'}, set()),
    'what_i_do': ({'h2_en', 'h2_he', 'p1_en', 'p1_he', 'p2_en', 'p2_he'}, {'eyebrow_en', 'eyebrow_he'}),
    'advisory': (set(), {'h2_en', 'h2_he', 'sub_en', 'sub_he'}),
    'faq': ({'q_en', 'a_en', 'q_he', 'a_he'}, set()),
}
OBJECTS = {'head', 'hero', 'intro', 'what_i_do', 'advisory'}
LISTS = {'services', 'faq', 'advisory_rows'}
HTML_FIELDS = {'what_i_do.p1_en', 'what_i_do.p1_he', 'what_i_do.p2_en', 'what_i_do.p2_he'}
# (field, min, max) in characters; the minimum and maximum read the English, the hero lines both languages
CHAR_LIMITS = [
    ('head.title', 30, 70), ('head.description', 70, 165), ('head.og_title', 1, 70), ('head.og_description', 1, 160),
    ('hero.l1_en', 1, 18), ('hero.l1_he', 1, 18), ('hero.l2_en', 1, 18), ('hero.l2_he', 1, 18),
    ('intro.h1_en', 40, 110), ('intro.line_en', 1, 32), ('intro.eyebrow_en', 1, 24), ('intro.statement_en', 60, 160),
    ('what_i_do.eyebrow_en', 1, 24), ('what_i_do.h2_en', 1, 120), ('advisory.h2_en', 1, 90), ('advisory.sub_en', 1, 200),
    ('cta_en', 40, 140), ('mail_subject', 8, 60),
]
WORD_LIMITS = [('what_i_do.p1_en', 40, 160), ('what_i_do.p2_en', 40, 160)]
SERVICE_DESC_MAX = 90
FAQ_COUNT = (5, 7)
FAQ_ANSWER_WORDS = (40, 90)
QUESTION_MAX = 110
HEBREW_SHARE = 0.6
ROWS_COUNT = (3, 8)
HUBS = ('/advisory/', '/projects/')
STUBS = ('2', 'about', 'our-team', 'our-team-1', 'contact', 'questions')
RESERVED = {'2', 'about', 'advisory', 'art-curator-new-jersey', 'art-curator-new-york', 'contact', 'content', 'css', 'fonts',
            'for-advisors', 'for-brokers', 'for-designers', 'guide', 'images', 'js', 'museum', 'our-team', 'our-team-1',
            'projects', 'questions', 'radar', 'templates', 'tools', 'videos'}

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
    for key in ('head', 'hero', 'intro', 'what_i_do', 'advisory'):
        for k, s in (v.get(key) or {}).items():
            out.append((f'{key}.{k}', s))
    for i, item in enumerate(v.get('services') or []):
        for k, s in (item if isinstance(item, dict) else {}).items():
            out.append((f'services[{i}].{k}', s))
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
    if label.endswith('_en') or label.startswith('head.') or label == 'mail_subject':
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
        return [f'{label}: {href} is a buyer variant; variants are never linked']
    target = os.path.join(ROOT, rel, 'index.html')
    if not os.path.exists(target):
        return [f'{label}: {href} is not a page on the site']
    page = open(target, encoding='utf-8').read()
    if 'name="robots" content="noindex"' in page:
        return [f'{label}: {href} is a noindex page']
    if frag and f'id="{frag}"' not in page:
        return [f'{label}: {href} has no id="{frag}" on that page']
    return []


def html_problems(label, s, variant_paths):
    """what_i_do.p1 and p2: a, em and strong only, balanced, links checked. Returns (problems, hrefs)."""
    problems, hrefs, depth = [], [], {}
    for close, name, attrs in TAG.findall(s):
        name = name.lower()
        if name not in ('a', 'em', 'strong'):
            problems.append(f'{label}: <{name}> is not allowed (a, em, strong only)')
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
            if k in (required | optional) - OBJECTS - LISTS and not (isinstance(s, str) and s):
                fails.append(f'{where}{k}: must be a non-empty string')
    keys(v, '', '')
    for name in sorted(OBJECTS):
        if name in v:
            keys(v[name], name, f'{name}.')
    for name in ('services', 'faq'):
        items = v.get(name)
        if name in v and not isinstance(items, list):
            fails.append(f'{name} must be a list')
            continue
        for i, item in enumerate(items or []):
            keys(item, name, f'{name}[{i}].')
    if isinstance(v.get('services'), list) and len(v['services']) != 4:
        fails.append(f'services: exactly 4 entries, one per service column (found {len(v["services"])})')
    v = dict(v)  # a normalized copy: what is missing or of the wrong type is reported above, empty below
    for k in OBJECTS:
        v[k] = v[k] if isinstance(v.get(k), dict) else {}
    for k in ('services', 'faq'):
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
    for name in ('hero', 'intro', 'what_i_do', 'advisory'):
        twins(v[name] if isinstance(v[name], dict) else {}, f'{name}.')
    for name in ('services', 'faq'):
        for i, item in enumerate(v[name]):
            if isinstance(item, dict):
                twins(item, f'{name}[{i}].')

    variant_paths = [vpath] + [o.get('path') for _, o in peers if isinstance(o.get('path'), str)]
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
        if label in HTML_FIELDS:
            problems, found = html_problems(label, s, variant_paths)
            fails.extend(problems)
            hrefs[label] = set(found)
        elif TAG.search(s) or re.search(r'<[A-Za-z!/]', s) or ENTITY.search(s):
            fails.append(f'{label}: HTML or an HTML entity; plain text here (HTML only in what_i_do.p1 and p2), write & and quotes as they are')
        # k: Stav speaks as "I"
        if lang == 'en' and label != 'mail_subject' and not re.search(r'\.q_en$', label):
            found = sorted(set(WE.findall(re.sub(r'<[^>]+>', ' ', s))))
            if found:
                warns.append(f'{label}: {", ".join(found)} (Stav speaks as "I"; fine if it means her and the client)')
    for p in ('p1', 'p2'):
        en, he = hrefs.get(f'what_i_do.{p}_en'), hrefs.get(f'what_i_do.{p}_he')
        if en is not None and he is not None and en != he:
            fails.append(f'what_i_do.{p}: the English and Hebrew link to different pages ({sorted(en)} and {sorted(he)})')

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
