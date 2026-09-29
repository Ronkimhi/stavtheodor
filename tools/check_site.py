#!/usr/bin/env python3
"""The gates every build must pass. Run from the repo root (python3 build.py runs it last).

  dashes      no em or en dash in the chrome, the templates, the data files, the docs or any
              page outside museum/ (post content authored in content/posts.html is Stav's text
              and is not rewritten by the build, so article bodies and timeline entries are skipped)
  phones      no phone number anywhere outside museum/ (AGENTS.md content rule 6)
  twins       every generated page has the same number of English and Hebrew twins
  anchors     index.html carries every id other pages link to
  links       every internal href and src on every page resolves to a file (or an id on index.html)
  jsonld      every ld+json block parses
  faq         the visible FAQ equals the FAQPage schema, word for word, on the homepage and on
              every buyer variant
  noindex     the homepage, the generated pages and the buyer variants (since 2026-09-28, Ron)
              are indexable; /2/, the old stubs and 404.html are not
  posts       index.html carries no post article (posts live in content/posts.html)
  removed     nothing references the assets removed on 2026-09-26, and they are gone; no image in
              the tree is one of the AI-marked photos removed on 2026-09-28 (matched by content hash,
              so a renamed copy is caught too; the site copies and the video project's masters)
  lang        every page outside museum/ opens in English: <html lang="en">, <body class="lang-en">,
              and at least 90% of the words a reader sees with the switch on English are Latin
              (the Hebrew twins, data-l="he" / lang="he" / .post-title-he, are dropped the way
              the stylesheet hides them; tools/check_render.js is the same test in a real browser)
  schema      what Google's Rich Results Test checks, reproduced locally: FAQPage questions with
              answers, BreadcrumbList positions and absolute items, BlogPosting headline/date/author,
              Service name/provider/areaServed, the entity graph (Person and ProfessionalService with
              geo, address, https sameAs), no underscore keys leaking, every on-site URL resolving
  sitemap     sitemap.xml is an index over child sitemaps; every indexable page is listed in exactly
              one child, every loc resolves to a file, and no noindex page is listed
  variants    the buyer pages (content/variants/<id>.json, rendered by build-home.py at /<path>/):
              every one is built, indexable with a self canonical (2026-09-28) and in exactly one
              sitemap; the homepage's #industries section links each exactly once; other links to
              one come only from its paired pages (VARIANT_LINKERS) and nowhere else; llms.txt and
              answers.md name every one; no noindex page is left over that is not a stub;
              the pages themselves go through twins, links, jsonld, schema, faq, noindex and lang

Exit 1 on any failure.
"""
import glob
import html as H
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SKIP_DIRS = {'.git', 'museum', '__pycache__', 'node_modules', '.perf'}  # .perf: gitignored Lighthouse reports (tools/perf.sh)
GATE_FILES = ('tools/check_site.py', 'tools/check_pages.py')  # they carry the patterns they hunt
DASH = re.compile('[\\u2013\\u2014]')
PHONE = re.compile(r'\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1[ (]?\d{3}|\(\d{3}\) ?\d{3}[ .-]\d{4}|\b0\d{2}[ -]?\d{7}\b|\+972')
SITE = 'https://stavtheodor.com'
GENERATED_DIRS = ('radar', 'advisory', 'projects', 'for-designers', 'for-brokers', 'for-advisors', 'guide', 'art-curator-new-jersey', 'art-curator-new-york')
STUB_DIRS = ('2', 'about', 'our-team', 'our-team-1', 'contact', 'questions')  # redirect stubs written by build-home.py: noindex, never indexable pages
HOME_ANCHORS = ('about', 'what-i-do', 'portfolio', 'film', 'projects', 'advisory', 'museum', 'radar', 'posts', 'faq', 'contact')
REMOVED = ('images/portfolio/', 'theodora-film-2026-09.mp4')
# The first 16 hex digits of the SHA-256 of every Gemini-marked (or Gemini-processed) photo removed on 2026-09-28:
# the nine project photos and three homepage copies, and the masters they were cut from. None may come back, under any name.
BANNED_IMAGES = {
    '3f4cc55eb3845d10', 'c9fd6d649602759f', 'f5e14bd0de8efe4a', 'e117edd3a4973767', '95afc52c90fca405', '6e68c2dbc6d8738b',
    '8dfb8935fa61135a', 'dfa0d6c9e46035c1', '90ec74ddff1f3de2', '8514f7097561228d', 'c976f3f6ce8144bd', '6e2497d4663bb830',
    '718c475ac20d8e15', 'd2725a41bbd80339', 'dea7bfad1d6585e2', '9f87b708d526a6cf', '4f06600f6a0706f9', '3631076c645d4096',
    '21db47b8abf26e62', 'b78ea3fe28ec1622', 'f6070dab13b23b81',
}
AGENT_FILES = ('llms.txt', 'answers.md')  # every buyer page is named in these (2026-09-28)
# The pages allowed to link a buyer page besides the homepage's #industries section (2026-09-28): the
# pages each one overlaps with, which link it both ways (/designers/ and /for-designers/, /wealth-managers/
# and /for-advisors/, the hotel and office advisory pages).
VARIANT_LINKERS = ('for-designers/index.html', 'for-advisors/index.html',
                   'advisory/art-for-hotels-and-hospitality/index.html', 'advisory/art-for-an-office-or-business/index.html')
fails = []


def fail(gate, msg):
    fails.append(f'{gate}: {msg}')


# The buyer variants (content/variants/<id>.json): {their page: their URL}. Indexable and in sitemap-pages.xml
# since 2026-09-28 (Ron); linked only from the homepage's #industries section.
VARIANTS = {}
for _f in sorted(glob.glob(os.path.join('content', 'variants', '*.json'))):
    try:
        _path = json.load(open(_f, encoding='utf-8'))['path'].strip('/')
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        fail('variants', f'{_f} has no readable path ({e}): run python3 tools/check_variants.py')
        continue
    VARIANTS[os.path.normpath(os.path.join(_path, 'index.html'))] = f'{SITE}/{_path}/'


def walk(exts):
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(exts):
                yield os.path.normpath(os.path.join(dirpath, f))


def read(path):
    return open(path, encoding='utf-8', errors='replace').read()


class VisibleText(HTMLParser):
    """The text a reader sees with the switch on English: an emulation of the stylesheet's
    body.lang-en rules (data-l="he", lang="he", .post-title-he and the English switch
    button are hidden), with scripts, styles and the <head> left out."""
    VOID = {'img', 'br', 'hr', 'meta', 'link', 'input', 'source', 'wbr', 'area', 'base', 'col', 'embed', 'param', 'track'}
    SKIP = {'script', 'style', 'noscript', 'template', 'head', 'title'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.hidden, self.skipped, self.parts = [], 0, 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        classes = (a.get('class') or '').split()
        hide = (a.get('data-l') == 'he' or (a.get('lang') == 'he' and tag != 'html') or 'post-title-he' in classes
                or (tag == 'button' and a.get('data-lang') == 'en'))
        skip = tag in self.SKIP
        self.stack.append((tag, hide, skip))
        self.hidden += hide
        self.skipped += skip

    def handle_endtag(self, tag):
        if tag in self.VOID or not any(t == tag for t, _, _ in self.stack):
            return  # a self-closing <img /> or a stray end tag must not pop an open block
        while self.stack:
            t, hide, skip = self.stack.pop()
            self.hidden -= hide
            self.skipped -= skip
            if t == tag:
                break

    def handle_data(self, data):
        if not self.hidden and not self.skipped:
            self.parts.append(data)


LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
HEBREW_WORD = re.compile(r'[֐-׿][֐-׿\'"׳״\-]*')


def visible_language(text):
    """(latin words, hebrew words) in what the English reader sees."""
    v = VisibleText()
    v.feed(text)
    seen = ' '.join(v.parts)
    return len(LATIN_WORD.findall(seen)), len(HEBREW_WORD.findall(seen))


def on_site_file(url):
    """The file a stavtheodor.com URL serves, or None for an off-site URL."""
    if not url.startswith(SITE + '/'):
        return None
    rel = url[len(SITE) + 1:].split('#')[0].split('?')[0]
    if rel == '' or rel.endswith('/'):
        rel += 'index.html'
    return rel


def check_schema(path, block, n):
    """The Rich Results Test, the part of it that runs without Google: required fields per type,
    sequential breadcrumbs, absolute URLs that resolve, no editor keys on the page."""
    def bad(msg):
        fail('schema', f'{path} block {n}: {msg}')

    def types(d):
        t = d.get('@type') if isinstance(d, dict) else None
        return t if isinstance(t, list) else [t] if t else []

    def walk(node, trail=''):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith('_'):
                    bad(f'editor key {trail}{k} leaked onto the page')
                if k in ('url', 'item', 'image', 'logo', 'mainEntityOfPage', 'sameAs') and isinstance(v, str) and v.startswith('http'):
                    rel = on_site_file(v)
                    if rel and not os.path.exists(rel):
                        bad(f'{trail}{k} {v} does not resolve')
                    if not v.startswith('https://'):
                        bad(f'{trail}{k} {v} is not https')
                walk(v, f'{trail}{k}.')
        elif isinstance(node, list):
            for v in node:
                walk(v, trail)

    walk(block)
    nodes = block.get('@graph', [block]) if isinstance(block, dict) else []
    for d in nodes:
        t = types(d)
        if 'FAQPage' in t:
            qs = d.get('mainEntity') or []
            if not qs:
                bad('FAQPage without questions')
            for q in qs:
                if 'Question' not in types(q) or not q.get('name') or not (q.get('acceptedAnswer') or {}).get('text'):
                    bad('FAQPage question without a name or an answer text')
        if 'BreadcrumbList' in t:
            items = d.get('itemListElement') or []
            if not items:
                bad('BreadcrumbList without items')
            for i, it in enumerate(items, 1):
                if it.get('position') != i or not it.get('name') or not str(it.get('item', '')).startswith('https://'):
                    bad(f'BreadcrumbList item {i} needs position {i}, a name and an absolute item URL')
        if 'BlogPosting' in t:
            for k in ('headline', 'datePublished', 'author', 'url', 'mainEntityOfPage'):
                if not d.get(k):
                    bad(f'BlogPosting without {k}')
        if 'Service' in t:
            for k in ('name', 'provider', 'areaServed', 'serviceType'):
                if not d.get(k):
                    bad(f'Service without {k}')
        if 'Person' in t and d.get('@id'):
            for k in ('name', 'url', 'jobTitle', 'sameAs'):
                if not d.get(k):
                    bad(f'Person without {k}')
        if 'ProfessionalService' in t and d.get('@id'):
            for k in ('name', 'url', 'address', 'sameAs', 'areaServed', 'email'):
                if not d.get(k):
                    bad(f'ProfessionalService without {k}')
            geo = d.get('geo') or {}
            if not (isinstance(geo.get('latitude'), (int, float)) and isinstance(geo.get('longitude'), (int, float))):
                bad('ProfessionalService without numeric geo coordinates')
            if 'telephone' in d:
                bad('ProfessionalService carries a telephone (content rule 6)')


def chrome_only(text, path):
    """What the build wrote itself: scripts, post articles and timeline entries stripped."""
    text = re.sub(r'<script.*?</script>', '', text, flags=re.S)
    if path.endswith('.html'):
        text = re.sub(r'<article class="post.*?</article>', '', text, flags=re.S)
        text = re.sub(r'<a class="entry reveal".*?</a>', '', text, flags=re.S)
        text = re.sub(r'<!-- POST TEMPLATE.*?-->', '', text, flags=re.S)
    return text


# ---- dashes and phones, over every text file the site ships or builds from
for path in walk(('.html', '.txt', '.md', '.json', '.py', '.css', '.js', '.xml')):
    if path in GATE_FILES:
        continue
    s = read(path)
    body = chrome_only(s, path)
    if path == 'AGENTS.md':  # rule 3.2 spells the two characters it bans; the Work Log is other sessions' history
        body = body.split('## 7. Work Log')[0].replace('No em dashes (\u2014) and no en dashes (\u2013)', '')
    if path.startswith('radar' + os.sep) and path != os.path.join('radar', 'index.html'):
        body = re.sub(r'<head>.*?</head>', '', body, flags=re.S)  # title and meta carry the post's own headline
    m = DASH.search(body)
    if m:
        fail('dashes', f'{path}: {body[max(0, m.start() - 40):m.end() + 20]!r}')
    m = PHONE.search(s)
    if m:
        fail('phones', f'{path}: {m.group(0)!r}')

# ---- pages
pages = ['index.html', '404.html'] + [p for p in walk(('.html',)) if p.split(os.sep)[0] in GENERATED_DIRS + STUB_DIRS]
for path in VARIANTS:
    if os.path.exists(path):
        pages.append(path)
    else:
        fail('variants', f'{path} is missing: run python3 build.py')
pages = sorted(set(pages))
home = read('index.html')

for path in pages:
    s = read(path)
    is_stub = path.split(os.sep)[0] in STUB_DIRS or path in ('404.html',)
    must_noindex = is_stub  # the buyer variants are indexable since 2026-09-28
    if not is_stub:
        en, he = s.count('data-l="en"'), s.count('data-l="he"')
        if en == 0 or he == 0 or en != he:
            fail('twins', f'{path}: {en} en, {he} he')
    for i, block in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)):
        try:
            parsed = json.loads(block)
        except Exception as e:
            fail('jsonld', f'{path} block {i + 1}: {e}')
            continue
        if not is_stub:
            check_schema(path, parsed, i + 1)
    has_noindex = 'name="robots" content="noindex"' in s
    if must_noindex and not has_noindex:
        fail('noindex', f'{path} should be noindex')
    if not must_noindex and has_noindex:
        fail('noindex', f'{path} must be indexable')
    if not is_stub:
        if not re.search(r'<html lang="en"', s):
            fail('lang', f'{path}: <html lang="en"> missing')
        if not re.search(r'<body class="lang-en"', s):
            fail('lang', f'{path}: <body class="lang-en"> missing (English must be the default without JS)')
        if 'hreflang=' in s:
            fail('lang', f'{path}: hreflang tags were dropped on 2026-09-26, do not emit them')
        latin, hebrew = visible_language(s)
        share = latin / max(1, latin + hebrew)
        if share < 0.9:
            fail('lang', f'{path}: only {share:.0%} of visible words are Latin ({latin} Latin, {hebrew} Hebrew)')
    # the homepage's industries section (#industries, 2026-09-28) is the one place that may link a buyer variant
    ind = re.search(r'<section\b[^>]*\bid="industries"[^>]*>.*?</section>', s, re.S) if path == 'index.html' else None
    for m_link in re.finditer(r'\b(href|src)="([^"]+)"', s):
        attr, target = m_link.group(1), m_link.group(2)
        in_industries = bool(ind) and ind.start() <= m_link.start() < ind.end()
        if target.startswith(('http://', 'https://', 'mailto:', 'data:', 'tel:', '//')):
            if target.startswith('https://stavtheodor.com/'):
                target = target[len('https://stavtheodor.com'):]
            else:
                continue
        if target.startswith('#'):
            frag, rel_target = target[1:], None
        elif '#' in target:
            rel_target, frag = target.split('#', 1)
        else:
            rel_target, frag = target, None
        if rel_target is not None and rel_target != '':
            fs = rel_target.lstrip('/') if rel_target.startswith('/') else os.path.normpath(os.path.join(os.path.dirname(path), rel_target))
            fs = fs.split('?')[0]
            if fs == '' or os.path.isdir(fs):
                fs = os.path.join(fs, 'index.html') if fs else 'index.html'
            if os.path.normpath(fs) in VARIANTS and os.path.normpath(fs) != path and not in_industries and path not in VARIANT_LINKERS:
                fail('variants', f'{path} links to the buyer page {target} (only the homepage\'s #industries section and VARIANT_LINKERS may)')
            if not os.path.exists(fs):
                fail('links', f'{path} -> {target}')
                continue
            if frag and fs.endswith('.html') and f'id="{frag}"' not in read(fs):
                fail('links', f'{path} -> {target} (no id="{frag}" on {fs})')
        elif frag and f'id="{frag}"' not in s:
            fail('links', f'{path} -> {target} (no id="{frag}" on the page)')

# ---- the homepage
for a in HOME_ANCHORS:
    if f'id="{a}"' not in home:
        fail('anchors', f'index.html has no id="{a}"')
if '<article class="post' in home:
    fail('posts', 'index.html contains an Art Radar article; posts live in content/posts.html')


def faq_mirror(path):
    """The visible questions on a homepage-shaped page (index.html, a buyer variant) equal its FAQPage schema."""
    s = read(path)
    m = re.search(r'<script type="application/ld\+json">\s*(\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?)</script>', s, re.S)
    if not m:
        fail('faq', f'no FAQPage schema on {path}')
        return
    schema = [(q['name'], q['acceptedAnswer']['text']) for q in json.loads(m.group(1))['mainEntity']]
    visible = [(H.unescape(q).strip(), H.unescape(a).strip()) for q, a in re.findall(
        r'<details class="qa"[^>]*>\s*<summary><h3 class="serif"><span data-l="en">(.*?)</span>.*?<p class="body"><span data-l="en">(.*?)</span>', s, re.S)]
    if schema != visible:
        fail('faq', f'{path}: visible FAQ differs from the FAQPage schema ({len(schema)} schema, {len(visible)} visible)')


for path in ['index.html'] + sorted(p for p in VARIANTS if os.path.exists(p)):
    faq_mirror(path)

# ---- the homepage's industries section links every buyer variant once, and nothing links them elsewhere (above)
_home = read('index.html') if os.path.exists('index.html') else ''
_ind = re.search(r'<section\b[^>]*\bid="industries"[^>]*>.*?</section>', _home, re.S)
if VARIANTS and not _ind:
    fail('variants', 'index.html has no #industries section linking the buyer variants')
elif _ind:
    _links = re.findall(r'<a\b[^>]*\bhref="/([^"#?]*)"', _ind.group(0))
    for _p in VARIANTS:
        _want = os.path.dirname(_p).replace(os.sep, '/') + '/'
        if _links.count(_want) != 1:
            fail('variants', f'index.html #industries links /{_want} {_links.count(_want)} times, expected once')
    for _l in _links:
        if os.path.normpath(os.path.join(_l, 'index.html')) not in VARIANTS:
            fail('variants', f'index.html #industries links /{_l}, which is not a buyer variant')

# ---- the buyer variants are named nowhere an agent or a crawler reads a map of the site
for f in AGENT_FILES:
    if not os.path.exists(f):
        continue
    s = read(f)
    for url in VARIANTS.values():
        if url not in s:
            fail('variants', f'{f} does not name the buyer page {url}')

# ---- the sitemaps: an index, every indexable page once, every loc a file, nothing noindex
sitemap_index = read('sitemap.xml') if os.path.exists('sitemap.xml') else ''
if '<sitemapindex' not in sitemap_index:
    fail('sitemap', 'sitemap.xml is not a sitemap index (tools/build_sitemap.py writes it)')
listed = {}
for child_url in re.findall(r'<loc>([^<]+)</loc>', sitemap_index):
    child = on_site_file(child_url)
    if not child or not os.path.exists(child):
        fail('sitemap', f'child sitemap {child_url} is missing')
        continue
    for loc in re.findall(r'<loc>([^<]+)</loc>', read(child)):
        listed.setdefault(loc, []).append(child)
_all_locs = [loc for child_url in re.findall(r'<loc>([^<]+)</loc>', sitemap_index)
             for loc in (re.findall(r'<loc>([^<]+)</loc>', read(on_site_file(child_url))) if on_site_file(child_url) and os.path.exists(on_site_file(child_url)) else [])]
for _url in VARIANTS.values():
    if _all_locs.count(_url) != 1:
        fail('variants', f'the buyer page {_url} is listed {_all_locs.count(_url)} times across the sitemaps, expected once')
for loc, where in listed.items():
    if len(where) > 1:
        fail('sitemap', f'{loc} is listed in {len(where)} sitemaps')
    rel = on_site_file(loc)
    if not rel or not os.path.exists(rel):
        fail('sitemap', f'{loc} does not resolve to a file')
    elif 'name="robots" content="noindex"' in read(rel):
        fail('sitemap', f'{loc} is noindex and must not be listed')
for path in walk(('.html',)):
    if path == '404.html' or path.split(os.sep)[0] in STUB_DIRS:
        continue
    s = read(path)
    if 'data-subject="' in s and path not in VARIANTS:
        fail('variants', f'{path} is a buyer variant page but not a current variant: stale variant folder? git rm -r {os.path.dirname(path) or path}')
        continue
    if 'name="robots" content="noindex"' in s:
        fail('variants', f'{path} is noindex but not a stub: a stale buyer page folder? git rm -r {os.path.dirname(path) or path}')
        continue
    if not path.endswith('index.html'):
        continue  # only directory index pages are site URLs
    url = SITE + '/' + path[:-len('index.html')].replace(os.sep, '/')
    if url not in listed:
        fail('sitemap', f'{path} is indexable but in no sitemap')

# ---- removed assets: no reference anywhere, no file left
for path in walk(('.html', '.txt', '.md', '.py', '.json', '.css', '.js', '.xml')):
    if path in GATE_FILES or path == 'AGENTS.md':
        continue
    s = read(path)
    for r in REMOVED:
        if r in s:
            fail('removed', f'{path} references {r}')
for r in REMOVED:
    if os.path.exists(r.rstrip('/')) or os.path.exists(os.path.join('videos', r)):
        fail('removed', f'{r} still exists in the tree')

import hashlib
for path in walk(('.jpg', '.jpeg', '.png', '.webp')):
    if hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16] in BANNED_IMAGES:
        fail('removed', f'{path} is one of the AI-marked photos removed on 2026-09-28 (AGENTS.md Work Log): delete it')

gates = ['dashes', 'phones', 'twins', 'anchors', 'links', 'jsonld', 'schema', 'faq', 'noindex', 'posts', 'removed', 'lang', 'sitemap', 'variants']
if fails:
    print('\n'.join(sorted(set(fails))))
    print(f'\ncheck_site: {len(set(fails))} failure(s) across', ', '.join(sorted({f.split(":")[0] for f in fails})))
    sys.exit(1)
print('check_site: OK (' + ', '.join(gates) + f') over {len(pages)} pages')
