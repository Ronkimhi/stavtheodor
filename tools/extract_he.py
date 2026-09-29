#!/usr/bin/env python3
"""The Hebrew segment table: every translatable English and Hebrew pair in the site's sources, one JSON line each.

    python3 tools/extract_he.py                 writes the default path below
    python3 tools/extract_he.py <out.jsonl>     writes there instead

Read only: it never touches the site. Prints the rows per source file, the total Hebrew characters, and the
strings that have no twin (Hebrew without English, English without Hebrew). Exit 0 always.

A row: {id, file, field_or_locator, en, he, source_side, is_html, page_url}. source_side is "en" (the English
is the source the Hebrew is checked against). page_url is where the pair shows: a path, several paths joined by
" ", or "*" for the chrome every page carries.

Sources, the ones a Hebrew reader sees outside the Art Radar posts:
  content/pages/*.json       every <x>_he beside its <x>_en (title, lead, body, faq, hero_image, place, cta), and
                             the kicker, whose Hebrew comes from KICKER_HE in build-site-pages.py
  content/variants/*.json    every <x>_he beside its <x>_en, rooms included
  content/faq.json           the homepage questions
  content/spaces.json        cap_he beside cap_en, and alt_he beside alt_en (alt_he since 2026-09-29)
  templates/home.html        every data-l="he" element beside its data-l="en" sibling
  404.html                   hand written: each class="he" block beside the English block in the same position
  site_chrome.py, build-site-pages.py, build-post-pages.py, build-home.py
                             the hardcoded strings: T(en, he) calls, (en, he) tuples, en to he dicts, <x>_EN / <x>_HE
                             names, and literal data-l or lang="he" markup inside a string
Out of scope: content/posts.html (Stav's originals) and museum/ (English only by design).
"""
import ast
import glob
import html as H
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DEFAULT_OUT = '/Users/ronki/Documents/ron-brain/the-system-v8-ron/B-brain/09-knowledge/hebrew-qa/_audit/segments.jsonl'
HEB = re.compile('[֐-׿]')
LATIN = re.compile('[A-Za-z]')
TAG = re.compile(r'<[a-zA-Z/!]')
PY_FILES = {  # file: where its strings show
    'site_chrome.py': '*',
    'build-site-pages.py': '/advisory/ /projects/ and every page of content/pages',
    'build-post-pages.py': '/radar/ and every /radar/<slug>/',
    'build-home.py': '/',
}

rows = []
unpaired = []  # (file, locator, side, text)


def he_chars(s):
    return len(HEB.findall(s or ''))


def add(id_, file, loc, en, he, url, is_html=None):
    if is_html is None:
        is_html = bool(TAG.search(en or '') or TAG.search(he or ''))
    rows.append({'id': id_, 'file': file, 'field_or_locator': loc, 'en': en, 'he': he,
                 'source_side': 'en', 'is_html': is_html, 'page_url': url})


# ---------------------------------------------------------------- JSON sources

def walk_pairs(node, trail=''):
    """Yield (path, en_value, he_value, en_key_present, he_key_present) for every <x>_en / <x>_he key pair."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                yield from walk_pairs(v, f'{trail}.{k}' if trail else k)
        for k in node:
            if k.endswith('_he'):
                ek = k[:-3] + '_en'
                yield (f'{trail}.{k}' if trail else k), node.get(ek), node[k], ek in node, True
            elif k.endswith('_en') and k[:-3] + '_he' not in node:
                yield (f'{trail}.{k[:-3]}_he' if trail else k[:-3] + '_he'), node[k], None, True, False
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_pairs(v, f'{trail}[{i}]')


def json_source(path, prefix, url, skip=()):
    data = json.load(open(path, encoding='utf-8'))
    for loc, en, he, has_en, has_he in walk_pairs(data):
        if any(loc.endswith(s) for s in skip):
            continue
        if not has_he:
            unpaired.append((path, loc.replace('_he', '_en'), 'en only', en))
            continue
        if not has_en:
            unpaired.append((path, loc, 'he only', he))
        add(f'{prefix}#{loc}', path, loc, en if isinstance(en, str) else '', he if isinstance(he, str) else '', url)
    return data


def build_site_pages_consts():
    """KICKER_HE, SECTION_KICKER, SECTION_KICKER_HE from build-site-pages.py, read without running it."""
    tree = ast.parse(open('build-site-pages.py', encoding='utf-8').read())
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in ('KICKER_HE', 'SECTION_KICKER', 'SECTION_KICKER_HE'):
                out[n.targets[0].id] = ast.literal_eval(n.value)
    return out


def pages():
    k = build_site_pages_consts()
    for f in sorted(glob.glob('content/pages/*.json')):
        data = json.load(open(f, encoding='utf-8'))
        url = '/' + data['path'].strip('/') + '/'
        slug = os.path.basename(f)
        json_source(f, f'pages/{slug}', url)
        # the kicker: English in the JSON, Hebrew from the build's map (build-site-pages.py kickers())
        kicker = data.get('kicker', k['SECTION_KICKER'].get(data['section'], 'THEODORA'))
        he = data.get('kicker_he') or k['KICKER_HE'].get(kicker)
        loc = 'kicker (Hebrew from build-site-pages.py KICKER_HE)'
        if he is None and kicker == k['SECTION_KICKER'].get(data['section']):
            he = k['SECTION_KICKER_HE'].get(data['section'], 'THEODORA')
            loc = 'kicker (the section default, Hebrew from build-site-pages.py SECTION_KICKER_HE)'
        if he is None:
            he = k['SECTION_KICKER_HE'].get(data['section'], 'THEODORA')
            unpaired.append((f, 'kicker', 'en only (not in KICKER_HE, Hebrew falls back to the section kicker)',
                             f'{kicker} -> {he}'))
            loc = 'kicker (NOT in KICKER_HE: Hebrew is the section fallback)'
        add(f'pages/{slug}#kicker', f, loc, kicker, he, url, False)


def variants():
    for f in sorted(glob.glob('content/variants/*.json')):
        data = json.load(open(f, encoding='utf-8'))
        json_source(f, f'variants/{os.path.basename(f)}', '/' + data['path'].strip('/') + '/')


def faq():
    json_source('content/faq.json', 'faq.json', '/')


def spaces():
    users = {}
    for f in sorted(glob.glob('content/pages/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('before_after'):
            users.setdefault(d['before_after'], []).append('/' + d['path'].strip('/') + '/')
    data = json.load(open('content/spaces.json', encoding='utf-8'))['spaces']
    for key, s in data.items():
        url = ' '.join(users.get(key, [])) or '(unused)'
        add(f'spaces.json#{key}.cap_he', 'content/spaces.json', f'spaces.{key}.cap_he', s.get('cap_en', ''), s.get('cap_he', ''), url)
        if 'alt_he' in s:
            add(f'spaces.json#{key}.alt_he', 'content/spaces.json', f'spaces.{key}.alt_he', s.get('alt_en', ''), s['alt_he'], url)
        elif 'alt_en' in s:
            unpaired.append(('content/spaces.json', f'spaces.{key}.alt_en', 'en only', s['alt_en']))


# ---------------------------------------------------------------- HTML pairs (templates and literal markup)

class Elements(HTMLParser):
    """Every element with data-l, or lang="he" / lang="en", with its offsets and parent."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src = src
        self.lines = [0]
        for m in re.finditer('\n', src):
            self.lines.append(m.end())
        self.stack = []
        self.found = []

    def off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        start = self.off()
        end_tag = self.src.index('>', start) + 1
        lang = a.get('data-l') or (a.get('lang') if a.get('lang') in ('he', 'en') else None)
        el = {'tag': tag, 'attrs': a, 'lang': lang, 'start': start, 'inner': end_tag,
              'parent': id(self.stack[-1]) if self.stack else None, 'line': self.getpos()[0]}
        self.stack.append(el)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                el = self.stack[i]
                del self.stack[i:]
                el['close'] = self.off()
                el['end'] = self.src.index('>', el['close']) + 1
                if el['lang']:
                    self.found.append(el)
                return


def html_pairs(src):
    """(en_inner, he_inner, he_element, en_element) for each Hebrew element and its adjacent English sibling."""
    p = Elements(src)
    p.feed(src)
    els = sorted(p.found, key=lambda e: e['start'])
    by_end = {e['end']: e for e in els}
    by_start = {e['start']: e for e in els}
    out, used = [], set()

    def adjacent(e, before):
        if before:
            j = e['start']
            while j > 0 and src[j - 1] in ' \t\r\n':
                j -= 1
            o = by_end.get(j)
        else:
            j = e['end']
            while j < len(src) and src[j] in ' \t\r\n':
                j += 1
            o = by_start.get(j)
        return o if o and o['lang'] == 'en' and o['parent'] == e['parent'] else None

    for e in els:
        if e['lang'] != 'he':
            continue
        en = adjacent(e, True) or adjacent(e, False)
        if en is None and 'data-l' not in e['attrs']:
            # a plain lang="he" block after an untagged English sibling (the redirect stub)
            j = e['start']
            while j > 0 and src[j - 1] in ' \t\r\n':
                j -= 1
            m = re.search(r'<(\w+)[^>]*>((?:(?!<\1\b).)*?)</\1>$', src[:j], re.S)
            en_inner = m.group(2) if m else ''
            out.append((en_inner, src[e['inner']:e['close']], e, None))
            continue
        if en:
            used.add(id(en))
        out.append((src[en['inner']:en['close']] if en else None, src[e['inner']:e['close']], e, en))
    lonely_en = [e for e in els if e['lang'] == 'en' and 'data-l' in e['attrs'] and id(e) not in used]
    return out, lonely_en


def marker_at(src, pos):
    """The <!--variant:NAME--> region a template offset sits in, if any."""
    last = None
    for m in re.finditer(r'<!--(/?)variant:([a-z0-9_]+)-->', src[:pos]):
        last = None if m.group(1) else m.group(2)
    return last


def home_template():
    f = 'templates/home.html'
    src = open(f, encoding='utf-8').read()
    pairs, lonely = html_pairs(src)
    for i, (en, he, e, _) in enumerate(pairs, 1):
        mk = marker_at(src, e['start'])
        loc = f'line {e["line"]}, <{e["tag"]}>' + (f', variant region {mk}' if mk else '')
        if en is None:
            unpaired.append((f, loc, 'he only', he))
            en = ''
        add(f'home.html#pair-{i}', f, loc, en, he, '/' if not mk else '/ (and every buyer variant without its own ' + mk + ')')
    for e in lonely:
        unpaired.append((f, f'line {e["line"]}', 'en only', src[e['inner']:e['close']]))


def page_404():
    """404.html is written by hand: the English blocks above the <hr>, their Hebrew twins (class="he") below it, in order."""
    f = '404.html'
    src = open(f, encoding='utf-8').read()
    top, _, bottom = src.partition('<hr>')
    en = re.findall(r'<(h1|p)>(.*?)</\1>', top, re.S)
    he = re.findall(r'<(h1|p) class="he"[^>]*>(.*?)</\1>', bottom, re.S)
    for i, ((t1, e), (t2, h)) in enumerate(zip(en, he), 1):
        add(f'404.html#pair-{i}', f, f'<{t2} class="he"> number {i} after the <hr>', e.strip(), h.strip(), '/404.html')
    for extra in he[len(en):]:
        unpaired.append((f, extra[0], 'he only', extra[1]))
    for extra in en[len(he):]:
        unpaired.append((f, extra[0], 'en only', extra[1]))


# ---------------------------------------------------------------- hardcoded strings in the build scripts

def str_text(node):
    """A string constant, or an f-string with {name} for simple fields and {...} for the rest."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                out.append(v.value)
            else:
                e = v.value
                out.append('{' + ast.unparse(e) + '}' if isinstance(e, (ast.Name, ast.Attribute)) else '{...}')
        return ''.join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = str_text(node.left), str_text(node.right)
        return None if a is None or b is None else a + b
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'escape' and node.args:
        return str_text(node.args[0])
    if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
        return '{' + ast.unparse(node) + '}'
    return None


def py_source(f, url):
    src = open(f, encoding='utf-8').read()
    tree = ast.parse(src)
    parent, scope = {}, {}

    def mark(n, sc_name):
        for c in ast.iter_child_nodes(n):
            parent[c] = n
            name = sc_name
            if isinstance(c, (ast.FunctionDef, ast.ClassDef)):
                name = c.name
            elif isinstance(c, ast.Assign) and isinstance(c.targets[0], ast.Name) and sc_name == '<module>':
                name = c.targets[0].id
            scope[c] = name
            mark(c, name)
    mark(tree, '<module>')
    names = {}  # module level NAME: value node, for <x>_EN / <x>_HE and SECTION_KICKER style twins
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            names[n.targets[0].id] = n.value
    counter = {}

    def rid(node):
        s = scope.get(node, '<module>')
        counter[s] = counter.get(s, 0) + 1
        return f'{os.path.basename(f)}#{s}.{counter[s]}'

    def is_he(node):
        t = str_text(node) if isinstance(node, (ast.Constant, ast.JoinedStr)) else None
        return t is not None and HEB.search(t) is not None

    nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.Constant, ast.JoinedStr))]
    nodes.sort(key=lambda n: (n.lineno, n.col_offset))
    for n in nodes:
        if not is_he(n):
            continue
        if isinstance(parent.get(n), ast.JoinedStr):  # a piece of an f-string: handled with the whole f-string
            continue
        top = n
        while isinstance(parent.get(top), ast.BinOp):  # 'פרויקטים · ' + kicker_he: the whole sum is the string
            top = parent[top]
        t = str_text(top)
        if t is None:
            top, t = n, str_text(n)
        p = parent.get(top)
        loc = f'line {n.lineno}, in {scope.get(n, "<module>")}'
        # 0. a script: Hebrew in a JS ternary beside its English ('he' ? 'הועתק' : 'Copied')
        if '<script' in t:
            for m in re.finditer(r"'([^'\n]*[\u0590-\u05ff][^'\n]*)'\s*:\s*'([^'\n]*)'", t):
                add(rid(n), f, loc + ', JS string', m.group(2), m.group(1), url, False)
            if 'data-l="he"' not in t and 'lang="he"' not in t:
                continue
        # 1. literal bilingual markup inside the string
        if 'data-l="he"' in t or 'lang="he"' in t:
            pairs, lonely = html_pairs(t)
            rest = t
            for en, he, e, _ in pairs:
                if HEB.search(he) or not en:
                    add(rid(n), f, loc + f' (markup, <{e["tag"]}>)', en or '', he, url)
                    if en is None:
                        unpaired.append((f, loc, 'he only', he))
                rest = rest.replace(he, '')
            for frag in re.findall(r'[^<>"{}]*[\u0590-\u05ff][^<>"{}]*', rest):
                unpaired.append((f, loc, 'he only (inside markup, no twin: a label or a bilingual attribute)', frag.strip()))
            continue
        # 2. T(en, he)
        if isinstance(p, ast.Call) and (getattr(p.func, 'id', None) == 'T' or getattr(p.func, 'attr', None) == 'T') \
                and len(p.args) >= 2 and p.args[1] is top:
            add(rid(n), f, loc + ', T()', str_text(p.args[0]) or '', t, url)
            continue
        # 3. a tuple: the nearest earlier string without Hebrew is its English
        if isinstance(p, ast.Tuple):
            i = p.elts.index(n)
            en = None
            for j in range(i - 1, -1, -1):
                tj = str_text(p.elts[j])
                if tj is not None and not HEB.search(tj):
                    en = tj
                    break
            if en is not None:
                add(rid(n), f, loc + f', tuple item {i}', en, t, url)
                continue
        # 4. a dict value: the key, or the same key of the English twin dict (SECTION_KICKER_HE -> SECTION_KICKER)
        if isinstance(p, ast.Dict) and n in p.values:
            key = p.keys[p.values.index(n)]
            kt = str_text(key) if key is not None else None
            holder = scope.get(p, '')
            twin = names.get(holder[:-3]) if holder.endswith('_HE') else None
            if isinstance(twin, ast.Dict):
                for k2, v2 in zip(twin.keys, twin.values):
                    if k2 is not None and str_text(k2) == kt:
                        add(rid(n), f, loc + f', {holder}[{kt!r}] beside {holder[:-3]}', str_text(v2) or '', t, url)
                        break
                else:
                    unpaired.append((f, loc, 'he only', t))
                continue
            if kt is not None:
                add(rid(n), f, loc + f', dict key {kt!r}', kt, t, url)
                continue
        # 5. NAME_HE = "..." beside NAME_EN
        if isinstance(p, ast.Assign) and isinstance(p.targets[0], ast.Name) and p.targets[0].id.endswith('_HE'):
            en_node = names.get(p.targets[0].id[:-3] + '_EN')
            if en_node is not None:
                add(rid(n), f, loc + f', {p.targets[0].id} beside {p.targets[0].id[:-3]}_EN', str_text(en_node) or '', t, url)
                continue
        unpaired.append((f, loc, 'he only (no English twin found; label, regex or aria text)', t))


# ---------------------------------------------------------------- main

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    pages()
    variants()
    faq()
    spaces()
    home_template()
    page_404()
    for f, url in PY_FILES.items():
        py_source(f, url)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    per = {}
    for r in rows:
        key = r['file'] if not r['file'].startswith('content/pages/') and not r['file'].startswith('content/variants/') \
            else os.path.dirname(r['file']) + '/*.json'
        c = per.setdefault(key, [0, 0])
        c[0] += 1
        c[1] += he_chars(r['he'])
    print(f'extract_he: {len(rows)} rows -> {out}')
    for k in sorted(per):
        print(f'  {k:32} {per[k][0]:5} rows {per[k][1]:7} Hebrew chars')
    print(f'  {"total":32} {len(rows):5} rows {sum(v[1] for v in per.values()):7} Hebrew chars')
    print(f'\nno twin ({len(unpaired)}):')
    for f, loc, side, text in unpaired:
        text = re.sub(r'\s+', ' ', H.unescape(str(text)))
        print(f'  {f} | {loc} | {side} | {text[:110]}')


if __name__ == '__main__':
    main()
