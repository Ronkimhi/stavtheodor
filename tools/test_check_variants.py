#!/usr/bin/env python3
"""Self test for the FAQ answer links in tools/check_variants.py. Touches nothing here: it copies one buyer variant
into a temp folder, changes one FAQ answer, and runs the checker on that draft as `check_variants.py <file>` does.
It also tests the renderer, site_chrome.faq_answer_html (the visible FAQ of every buyer page and of the homepage,
whose content/faq.json no checker reads): only a site-path <a href="/..."> and its </a> pass, all else is escaped.

    python3 tools/test_check_variants.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
SOURCE = os.path.join(ROOT, 'content', 'variants', 'medical-practices.json')
FAQ = 5  # its own question about who installs, which names a certificate of insurance in both languages (the live answer links it)
EN, HE = 'certificate of insurance', 'אישור ביטוח'
PAGE = '/advisory/hanging-heavy-art-nyc-apartment-coi/'


def link(words, href=PAGE, attrs=''):
    return f'<a href="{href}"{attrs}>{words}</a>'


# (name, the English wrap, the Hebrew wrap, should it pass, text the output must carry); None leaves the words as they are
CASES = [
    ('no change', None, None, True, 'OK'),
    ('relative link in both languages', link(EN), link(HE), True, 'OK'),
    ('external href', link(EN, 'https://example.com/'), link(HE, 'https://example.com/'), False, 'not a site-relative link'),
    ('protocol-relative href', link(EN, '//example.com/'), link(HE, '//example.com/'), False, 'not a site-relative link'),
    ('homepage anchor', link(EN, '#faq'), link(HE, '#faq'), False, 'not a site-relative link'),
    ('mailto', link(EN, 'mailto:a@example.com'), link(HE, 'mailto:a@example.com'), False, 'mailto'),
    ('em', f'<em>{EN}</em>', f'<em>{HE}</em>', False, '<em> is not allowed (a only)'),
    ('strong', f'<strong>{EN}</strong>', f'<strong>{HE}</strong>', False, '<strong> is not allowed (a only)'),
    ('another attribute', link(EN, attrs=' target="_blank"'), link(HE, attrs=' target="_blank"'), False, 'exactly one href'),
    ('page that does not exist', link(EN, '/no-such-page/'), link(HE, '/no-such-page/'), False, 'is not a page on the site'),
    ('English only', link(EN), None, False, 'the English and Hebrew link to different pages'),
    ('unclosed link', f'<a href="{PAGE}">{EN}', f'<a href="{PAGE}">{HE}', False, 'unbalanced tags'),
]


# (name, answer text, the HTML faq_answer_html must return)
RENDER = [
    ('site link', f'a <a href="{PAGE}">{EN}</a> & b', f'a <a href="{PAGE}">{EN}</a> &amp; b'),
    ('protocol-relative', '<a href="//evil.com/">x</a>', '&lt;a href=&quot;//evil.com/&quot;&gt;x&lt;/a&gt;'),
    ('backslash', '<a href="/\\evil.com/">x</a>', '&lt;a href=&quot;/\\evil.com/&quot;&gt;x&lt;/a&gt;'),
    ('entity slash', '<a href="/&#47;evil.com/">x</a>', '&lt;a href=&quot;/&amp;#47;evil.com/&quot;&gt;x&lt;/a&gt;'),
    ('never closed', f'<a href="{PAGE}">x', f'&lt;a href=&quot;{PAGE}&quot;&gt;x'),
    ('stray close', 'x</a>', 'x&lt;/a&gt;'),
    ('plain text', 'Tom & "Jerry"', 'Tom &amp; &quot;Jerry&quot;'),
]


def render_cases():
    """faq_answer_html on each RENDER case; returns the number that failed."""
    sys.path.insert(0, ROOT)
    import site_chrome
    bad = 0
    for name, s, want in RENDER:
        got = site_chrome.faq_answer_html(s)
        if got != want:
            bad += 1
            print(f'FAIL render {name}: {got!r}, want {want!r}')
    return bad


def main():
    base = json.load(open(SOURCE, encoding='utf-8'))
    item = base['faq'][FAQ]
    for k in ('a_en', 'a_he'):  # every case starts from the plain words, whether or not the live answer links them
        item[k] = re.sub(r'<a href="[^"]*">(.*?)</a>', r'\1', item[k])
    assert EN in item['a_en'] and HE in item['a_he'], 'the chosen FAQ answer no longer carries the words this test wraps'
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        draft = os.path.join(d, os.path.basename(SOURCE))
        for name, en, he, passes, text in CASES:
            v = json.loads(json.dumps(base))
            if en is not None:
                v['faq'][FAQ]['a_en'] = item['a_en'].replace(EN, en, 1)
            if he is not None:
                v['faq'][FAQ]['a_he'] = item['a_he'].replace(HE, he, 1)
            with open(draft, 'w', encoding='utf-8') as f:
                json.dump(v, f, ensure_ascii=False)
            r = subprocess.run([sys.executable, os.path.join(TOOLS, 'check_variants.py'), draft], capture_output=True, text=True, cwd=ROOT)
            out = r.stdout + r.stderr
            if (r.returncode == 0) != passes or text not in out:
                bad += 1
                print(f'FAIL {name}\n{out}')
    bad += render_cases()
    total = len(CASES) + len(RENDER)
    print(f'test_check_variants: {"OK" if not bad else "FAILED"}, {total - bad} of {total} cases')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
