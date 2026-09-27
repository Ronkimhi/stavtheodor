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
  faq         the visible homepage FAQ equals the FAQPage schema, word for word
  noindex     the homepage and the generated pages are indexable; /2/ and the old stubs are not
  posts       index.html carries no post article (posts live in content/posts.html)
  removed     nothing references the assets removed on 2026-09-26, and they are gone
  lang        every page outside museum/ opens in English: <html lang="en">, <body class="lang-en">,
              and at least 90% of the words a reader sees with the switch on English are Latin
              (the Hebrew twins, data-l="he" / lang="he" / .post-title-he, are dropped the way
              the stylesheet hides them; tools/check_render.js is the same test in a real browser)

Exit 1 on any failure.
"""
import html as H
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SKIP_DIRS = {'.git', 'museum', '__pycache__', 'node_modules'}
GATE_FILES = ('tools/check_site.py', 'tools/check_pages.py')  # they carry the patterns they hunt
DASH = re.compile('[\\u2013\\u2014]')
PHONE = re.compile(r'\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1[ (]?\d{3}|\(\d{3}\) ?\d{3}[ .-]\d{4}|\b0\d{2}[ -]?\d{7}\b|\+972')
GENERATED_DIRS = ('radar', 'advisory', 'projects', 'for-designers', 'for-brokers', 'for-advisors', 'guide')
HOME_ANCHORS = ('about', 'portfolio', 'film', 'projects', 'advisory', 'museum', 'radar', 'posts', 'faq', 'contact')
REMOVED = ('images/portfolio/', 'theodora-film-2026-09.mp4')
fails = []


def fail(gate, msg):
    fails.append(f'{gate}: {msg}')


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
pages = ['index.html', '404.html'] + [p for p in walk(('.html',)) if p.split(os.sep)[0] in GENERATED_DIRS or p.startswith('2' + os.sep)]
pages = sorted(set(pages))
home = read('index.html')

for path in pages:
    s = read(path)
    is_stub = path.startswith('2' + os.sep) or path in ('404.html',)
    if not is_stub:
        en, he = s.count('data-l="en"'), s.count('data-l="he"')
        if en == 0 or he == 0 or en != he:
            fail('twins', f'{path}: {en} en, {he} he')
    for i, block in enumerate(re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)):
        try:
            json.loads(block)
        except Exception as e:
            fail('jsonld', f'{path} block {i + 1}: {e}')
    has_noindex = 'name="robots" content="noindex"' in s
    if is_stub and not has_noindex:
        fail('noindex', f'{path} should be noindex')
    if not is_stub and has_noindex:
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
    for attr, target in re.findall(r'\b(href|src)="([^"]+)"', s):
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
m = re.search(r'<script type="application/ld\+json">\s*(\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?)</script>', home, re.S)
if not m:
    fail('faq', 'no FAQPage schema on index.html')
else:
    schema = [(q['name'], q['acceptedAnswer']['text']) for q in json.loads(m.group(1))['mainEntity']]
    visible = [(H.unescape(q).strip(), H.unescape(a).strip()) for q, a in re.findall(
        r'<details class="qa"[^>]*>\s*<summary><h3 class="serif"><span data-l="en">(.*?)</span>.*?<p class="body"><span data-l="en">(.*?)</span>', home, re.S)]
    if schema != visible:
        fail('faq', f'visible FAQ differs from the FAQPage schema ({len(schema)} schema, {len(visible)} visible)')

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

gates = ['dashes', 'phones', 'twins', 'anchors', 'links', 'jsonld', 'faq', 'noindex', 'posts', 'removed', 'lang']
if fails:
    print('\n'.join(sorted(set(fails))))
    print(f'\ncheck_site: {len(set(fails))} failure(s) across', ', '.join(sorted({f.split(":")[0] for f in fails})))
    sys.exit(1)
print('check_site: OK (' + ', '.join(gates) + f') over {len(pages)} pages')
