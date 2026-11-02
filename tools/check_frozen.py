#!/usr/bin/env python3
"""Fails when a pull request changes a page listed in content/FROZEN.json.

    python3 tools/check_frozen.py                 in Actions: the PR comes from $GITHUB_EVENT_PATH
    python3 tools/check_frozen.py --event FILE    any JSON of the shape {"pull_request": {...}}

content/FROZEN.json is a list of page addresses: "hotels", "/guide/hotel-artwork/", "/" for the homepage,
"404.html" for a loose file. A freeze holds a page still while a test reads it, so it is a list, usually empty.

A page changed when its built file or its own source JSON (content/pages, content/variants, matched by "path")
differs. The gate proves the built files match the source, so a change to a shared template shows up here too.
The list is read from the base and from the PR together: a PR cannot lift a freeze and edit the page in one go.
Run from inside the repo. Exit 1 on a hit, 2 when the event cannot be read. Self test: tools/test_gate_checks.py
"""
import json
import os
import subprocess
import sys

FROZEN_FILE = 'content/FROZEN.json'
SOURCE_DIRS = ('content/pages/', 'content/variants/')


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout


def show(rev, path):
    """The file's bytes at rev, or None when it is not there."""
    try:
        return git('show', f'{rev}:{path}')
    except subprocess.CalledProcessError:
        return None


def load_json(rev, path):
    """The parsed file at rev. None when it is missing or does not parse."""
    raw = show(rev, path)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode('utf-8'))
    except ValueError:
        return None


def load_pr(argv):
    """The pull request from --event FILE or $GITHUB_EVENT_PATH. Exits 2 when there is none."""
    path = argv[argv.index('--event') + 1] if '--event' in argv else os.environ.get('GITHUB_EVENT_PATH')
    try:
        pr = json.load(open(path, encoding='utf-8'))['pull_request']
        pr['base']['sha'], pr['head']['sha'], pr['labels']
        return pr
    except (OSError, TypeError, ValueError, KeyError, IndexError) as e:
        print(f'cannot read the pull request from the event ({path}): {e!r}')
        sys.exit(2)


def changes(pr):
    """(merge base, head, [(status, path)]): what the PR itself changes, as GitHub's Files tab shows it."""
    head = pr['head']['sha']
    start = git('merge-base', pr['base']['sha'], head).decode().strip()
    parts = git('diff', '--name-status', '--no-renames', '-z', start, head).decode('utf-8').split('\0')
    return start, head, list(zip(parts[0::2], parts[1::2]))


def clean(entry):
    return entry.strip().strip('/')


def frozen_pages(pr):
    """Every frozen address in the base and in the PR. Raises ValueError on a list that is not a list of strings."""
    pages = set()
    for rev in (pr['base']['sha'], pr['head']['sha']):
        git('rev-parse', '--verify', '--quiet', rev + '^{commit}')  # a commit we cannot see fails here, never passes
        raw = show(rev, FROZEN_FILE)
        if raw is None:
            continue
        entries = json.loads(raw.decode('utf-8'))
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            raise ValueError(f'{FROZEN_FILE} at {rev} is not a list of strings')
        pages.update(clean(e) for e in entries)
    return pages


def page_addresses(start, head, path):
    """The page addresses a changed file belongs to."""
    if path == 'index.html':
        return {''}
    if path.endswith('/index.html'):
        return {path[:-len('/index.html')]}
    if path.endswith('.html'):
        return {path}
    if path.startswith(SOURCE_DIRS) and path.endswith('.json'):
        found = set()
        for rev in (start, head):
            data = load_json(rev, path)
            if isinstance(data, dict) and isinstance(data.get('path'), str):
                found.add(clean(data['path']))
        return found
    return set()


def main(argv):
    pr = load_pr(argv)
    try:
        frozen = frozen_pages(pr)
    except ValueError as e:
        print(f'check_frozen: FAIL, {e}')
        return 1
    if not frozen:
        print('check_frozen: OK, nothing is frozen')
        return 0
    start, head, changed = changes(pr)
    hits = sorted((path, a) for _, path in changed for a in page_addresses(start, head, path) if a in frozen)
    for path, address in hits:
        print(f'  {path} changes the frozen page /{address}')
    print(f'check_frozen: FAIL, {len(hits)} change(s) to frozen pages' if hits else f'check_frozen: OK, {len(frozen)} frozen, none changed')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
