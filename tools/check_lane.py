#!/usr/bin/env python3
"""Keeps a PR labelled auto-ship inside the lane that may merge with nobody looking.

    python3 tools/check_lane.py                 in Actions: the PR comes from $GITHUB_EVENT_PATH
    python3 tools/check_lane.py --event FILE    any JSON of the shape {"pull_request": {...}}

Without the label there is nothing to check. With it, the PR fails when it touches:
  - .github/, tools/, museum/tools/, CNAME or content/FROZEN.json (tools/sitemap-lastmod.json is exempt: the build
    writes it on every content change)
  - the Google Analytics tag, a robots meta tag (noindex) or a redirect in any page
  - a page's existence: deleting one is a person's call
  - a buyer page's opening line, intro.line_en or intro.line_he in content/variants/*.json (site rule W12), a new
    buyer page's line included

Pages are read as built, tag by tag and not line by line, so a title edit next to the tag does not trip it. The gate
proves the built pages match the source, so a change in a generator shows up here. ship.yml runs main's copy of this
file before merging, so a PR cannot talk its way past by editing it.
Run from inside the repo. Exit 1 on a hit, 2 when the event cannot be read. Self test: tools/test_gate_checks.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_frozen import changes, load_json, load_pr, show

LABEL = 'auto-ship'
GA_ID = 'G-4300MN0Q97'
LOCKED_DIRS = ('.github/', 'tools/', 'museum/tools/')
LOCKED_FILES = {'CNAME', 'content/FROZEN.json'}
GENERATED = {'tools/sitemap-lastmod.json'}
NOT_PAGES = ('content/', 'templates/', 'tools/', 'museum/tools/')
OPENING = ('line_en', 'line_he')

ROBOTS = re.compile(r'<meta\b[^>]*\bname\s*=\s*["\']?(?:robots|googlebot)\b[^>]*>', re.I)
REFRESH = re.compile(r'<meta\b[^>]*\bhttp-equiv\s*=\s*["\']?refresh\b[^>]*>|location\.replace\([^)]*\)', re.I)
SCRIPT = re.compile(r'<script\b[^>]*>.*?</script>', re.I | re.S)
GA_MARK = re.compile(r'googletagmanager|gtag\(\s*["\']config["\']|\bG-[A-Z0-9]{8,}\b')
GA_IDS = re.compile(r'\bG-[A-Z0-9]{8,}\b')


def ga_tags(html):
    return sorted(s for s in SCRIPT.findall(html) if GA_MARK.search(s))


def is_page(path):
    return path.endswith('.html') and not path.startswith(NOT_PAGES)


def page_hits(status, path, old, new):
    """What a change to one built page breaks. old and new are its text, None when the file is not on that side."""
    if status == 'D':
        return ['deletes a page']
    hits = []
    if old is None:  # a new page: it may carry the site's own tag, and nothing else
        strangers = sorted(set(GA_IDS.findall(' '.join(ga_tags(new)))) - {GA_ID})
        if strangers:
            hits.append(f'carries another analytics id: {", ".join(strangers)}')
    elif ga_tags(old) != ga_tags(new):
        hits.append('changes the Google Analytics tag')
    for pattern, what in ((ROBOTS, 'a robots meta tag (noindex)'), (REFRESH, 'a redirect')):
        before = sorted(pattern.findall(old or ''))
        if before != sorted(pattern.findall(new)):
            hits.append(f'{"adds" if old is None else "changes"} {what}')
    return hits


def opening_lines(data):
    intro = data.get('intro') if isinstance(data, dict) else None
    return {k: intro.get(k) for k in OPENING} if isinstance(intro, dict) else {}


def violations(start, head, changed):
    out = []
    for status, path in changed:
        if path in GENERATED:
            continue
        if path in LOCKED_FILES or path.startswith(LOCKED_DIRS):
            out.append(f'{path}: outside the lane')
        elif is_page(path):
            old = show(start, path) if status != 'A' else None
            new = show(head, path) if status != 'D' else None
            text = [None if b is None else b.decode('utf-8', 'replace') for b in (old, new)]
            out += [f'{path}: {hit}' for hit in page_hits(status, path, text[0], text[1])]
        elif path.startswith('content/variants/') and path.endswith('.json'):
            if opening_lines(load_json(start, path)) != opening_lines(load_json(head, path)):
                out.append(f'{path}: changes a buyer opening line (W12)')
    return out


def main(argv):
    pr = load_pr(argv)
    if LABEL not in {label['name'] for label in pr['labels']}:
        print(f'check_lane: OK, no {LABEL} label, a person merges this one')
        return 0
    start, head, changed = changes(pr)
    found = violations(start, head, changed)
    for line in found:
        print(f'  {line}')
    if found:
        print(f'check_lane: FAIL, {len(found)} change(s) a person must merge: remove the {LABEL} label or the change')
        return 1
    print(f'check_lane: OK, {len(changed)} file(s) inside the lane')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
