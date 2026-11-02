#!/usr/bin/env python3
"""Self test for tools/check_frozen.py, tools/check_lane.py and tools/ship_check.py. Needs git, touches nothing here:
it builds a small repo in a temp folder and opens each case as a branch on it.

    python3 tools/test_gate_checks.py
"""
import json
import os
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
from ship_check import decide

GA = ('<script async src="https://www.googletagmanager.com/gtag/js?id=G-4300MN0Q97"></script>'
      "<script>window.dataLayer=[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-4300MN0Q97');</script>")
PAGE = '<html><head><title>Old</title>' + GA + '</head><body><script>gtag("event","write_open")</script><p>Words</p></body></html>\n'
STUB = '<html><head><meta http-equiv="refresh" content="0; url=/about/"><meta name="robots" content="noindex"><script>location.replace("/about/");</script></head></html>\n'
VARIANT = {'id': 'hotels', 'path': 'hotels', 'intro': {'line_en': 'Agreed line.', 'line_he': 'Agreed he.', 'statement_en': 'Support.'}}
BASE = {
    'index.html': PAGE,
    'hotels/index.html': PAGE,
    'guide/frozen-one/index.html': PAGE,
    'about-old/index.html': STUB,
    'content/FROZEN.json': '[]\n',
    'content/pages/frozen-one.json': json.dumps({'path': 'guide/frozen-one', 'title_en': 'T'}),
    'content/variants/hotels.json': json.dumps(VARIANT),
    'tools/sitemap-lastmod.json': '{}\n',
    'tools/x.py': 'x = 1\n',
    'museum/tools/y.py': 'y = 1\n',
    'CNAME': 'stavtheodor.com\n',
    'readme.md': 'Mentions noindex and G-4300MN0Q97.\n',
}
FREEZE = {'content/FROZEN.json': '["/guide/frozen-one/", "/"]\n'}


def variant(**intro):
    return json.dumps({**VARIANT, 'intro': {**VARIANT['intro'], **intro}})


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(cwd, *args):
    r = run('git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', '-c', 'commit.gpgsign=false', *args, cwd=cwd)
    if r.returncode:
        raise RuntimeError(f'git {args}: {r.stderr}')
    return r.stdout.strip()


def write(repo, files):
    for path, text in files.items():
        full = os.path.join(repo, path)
        if text is None:
            os.remove(full)
        else:
            os.makedirs(os.path.dirname(full) or repo, exist_ok=True)
            with open(full, 'w', encoding='utf-8') as f:
                f.write(text)
    git(repo, 'add', '-A')
    git(repo, 'commit', '-q', '--allow-empty', '-m', 'change')
    return git(repo, 'rev-parse', 'HEAD')


class Repo:
    def __init__(self, folder, files):
        self.path = folder
        self.n = 0
        git(folder, 'init', '-q', '-b', 'main')
        self.base = write(folder, files)

    def check(self, script, files, labels=('auto-ship',)):
        """Opens files as a PR on the base, runs the script, returns (exit code, output)."""
        self.n += 1
        git(self.path, 'checkout', '-q', '-b', f'case-{self.n}', self.base)
        head = write(self.path, files)
        event = os.path.join(self.path, '.git', f'event-{self.n}.json')
        with open(event, 'w', encoding='utf-8') as f:
            json.dump({'pull_request': {'labels': [{'name': x} for x in labels],
                                        'base': {'sha': self.base, 'ref': 'main'}, 'head': {'sha': head}}}, f)
        r = run(sys.executable, os.path.join(TOOLS, script), '--event', event, cwd=self.path)
        git(self.path, 'checkout', '-q', 'main')
        return r.returncode, r.stdout + r.stderr


# (name, files changed, labels, should it pass, text the output must carry)
LABEL_ONLY = ('auto-ship',)
LANE = [
    ('title edit next to the tag', {'hotels/index.html': PAGE.replace('Old', 'New')}, LABEL_ONLY, True, 'inside the lane'),
    ('generated lastmod store', {'tools/sitemap-lastmod.json': '{"a": 1}\n'}, LABEL_ONLY, True, 'inside the lane'),
    ('new page with the site tag', {'new-page/index.html': PAGE}, LABEL_ONLY, True, 'inside the lane'),
    ('event tweak in another script', {'hotels/index.html': PAGE.replace('write_open', 'write_close')}, LABEL_ONLY, True, 'inside the lane'),
    ('docs that mention the tag', {'readme.md': 'noindex G-4300MN0Q97 http-equiv refresh\n'}, LABEL_ONLY, True, 'inside the lane'),
    ('variant, a field beside the line', {'content/variants/hotels.json': variant(statement_en='New support.')}, LABEL_ONLY, True, 'inside the lane'),
    ('no label: anything goes', {'.github/workflows/a.yml': 'x: 1\n', 'CNAME': 'other.com\n'}, ('other',), True, 'no auto-ship label'),
    ('workflow', {'.github/workflows/a.yml': 'x: 1\n'}, LABEL_ONLY, False, 'outside the lane'),
    ('tools', {'tools/x.py': 'x = 2\n'}, LABEL_ONLY, False, 'tools/x.py: outside the lane'),
    ('museum tools', {'museum/tools/y.py': 'y = 2\n'}, LABEL_ONLY, False, 'outside the lane'),
    ('CNAME', {'CNAME': 'other.com\n'}, LABEL_ONLY, False, 'CNAME: outside the lane'),
    ('lifting a freeze', {'content/FROZEN.json': '["a"]\n'}, LABEL_ONLY, False, 'outside the lane'),
    ('GA id', {'hotels/index.html': PAGE.replace('G-4300MN0Q97', 'G-AAAAAAAAAA')}, LABEL_ONLY, False, 'Google Analytics tag'),
    ('GA removed', {'hotels/index.html': PAGE.replace(GA, '')}, LABEL_ONLY, False, 'Google Analytics tag'),
    ('new page, another id', {'new-page/index.html': PAGE.replace('G-4300MN0Q97', 'G-AAAAAAAAAA')}, LABEL_ONLY, False, 'another analytics id'),
    ('noindex added', {'hotels/index.html': PAGE.replace('<title>', '<meta name="robots" content="noindex"><title>')}, LABEL_ONLY, False, 'noindex'),
    ('noindex removed', {'about-old/index.html': STUB.replace('<meta name="robots" content="noindex">', '')}, LABEL_ONLY, False, 'noindex'),
    ('new page with noindex', {'new-page/index.html': PAGE.replace('<title>', '<meta content="noindex" name="robots"><title>')}, LABEL_ONLY, False, 'noindex'),
    ('redirect target', {'about-old/index.html': STUB.replace('/about/', '/contact/')}, LABEL_ONLY, False, 'a redirect'),
    ('new redirect', {'moved/index.html': '<meta http-equiv="refresh" content="0; url=/x/">'}, LABEL_ONLY, False, 'a redirect'),
    ('page deleted', {'hotels/index.html': None}, LABEL_ONLY, False, 'deletes a page'),
    ('opening line', {'content/variants/hotels.json': variant(line_en='A search line.')}, LABEL_ONLY, False, 'W12'),
    ('opening line, Hebrew', {'content/variants/hotels.json': variant(line_he='Other.')}, LABEL_ONLY, False, 'W12'),
    ('new buyer page', {'content/variants/new.json': json.dumps(VARIANT)}, LABEL_ONLY, False, 'W12'),
]
FROZEN = [
    ('other page', {'hotels/index.html': PAGE.replace('Old', 'New')}, True, 'none changed'),
    ('frozen built page', {'guide/frozen-one/index.html': PAGE.replace('Old', 'New')}, False, 'frozen page /guide/frozen-one'),
    ('frozen source', {'content/pages/frozen-one.json': json.dumps({'path': 'guide/frozen-one', 'title_en': 'New'})}, False, 'frozen page /guide/frozen-one'),
    ('homepage', {'index.html': PAGE.replace('Old', 'New')}, False, 'frozen page /'),
    ('lift the freeze and edit in one PR', {'content/FROZEN.json': '[]\n', 'guide/frozen-one/index.html': PAGE.replace('Old', 'New')}, False, 'frozen page /guide/frozen-one'),
    ('list broken', {'content/FROZEN.json': '{"a": 1}\n'}, False, 'not a list of strings'),
]
SHA = 'a' * 40
REPO = 'owner/site'
GREEN = {'check_runs': [{'conclusion': 'success'}]}
OLD_MAIN = {'commit': {'committer': {'date': '2026-11-02T10:00:00Z'}}}
GATE_AT = '2026-11-02T11:00:00Z'


def pr(**over):
    base = {'number': 7, 'state': 'open', 'draft': False, 'labels': [{'name': 'auto-ship'}],
            'head': {'sha': SHA, 'repo': {'full_name': REPO}}, 'base': {'ref': 'main'}}
    return {**base, **over}


SHIP = [
    ('clean', [pr()], GREEN, OLD_MAIN, 'ship'),
    ('draft', [pr(draft=True)], GREEN, OLD_MAIN, 'skip'),
    ('draft field missing', [{k: v for k, v in pr().items() if k != 'draft'}], GREEN, OLD_MAIN, 'skip'),
    ('no label', [pr(labels=[{'name': 'other'}])], GREEN, OLD_MAIN, 'skip'),
    ('fork', [pr(head={'sha': SHA, 'repo': {'full_name': 'someone/site'}})], GREEN, OLD_MAIN, 'skip'),
    ('fork deleted', [pr(head={'sha': SHA, 'repo': None})], GREEN, OLD_MAIN, 'skip'),
    ('closed', [pr(state='closed')], GREEN, OLD_MAIN, 'skip'),
    ('head moved', [pr(head={'sha': 'b' * 40, 'repo': {'full_name': REPO}})], GREEN, OLD_MAIN, 'skip'),
    ('other base', [pr(base={'ref': 'release'})], GREEN, OLD_MAIN, 'skip'),
    ('two PRs on one head', [pr(), pr(number=8)], GREEN, OLD_MAIN, 'skip'),
    ('no PR', [], GREEN, OLD_MAIN, 'skip'),
    ('gate red', [pr()], {'check_runs': [{'conclusion': 'failure'}]}, OLD_MAIN, 'skip'),
    ('gate running', [pr()], {'check_runs': [{'conclusion': None}]}, OLD_MAIN, 'skip'),
    ('gate missing', [pr()], {'check_runs': []}, OLD_MAIN, 'skip'),
    ('main moved', [pr()], GREEN, {'commit': {'committer': {'date': '2026-11-02T12:00:00Z'}}}, 'stale'),
]


def main():
    bad = 0

    def report(ok, group, name, detail=''):
        nonlocal bad
        if not ok:
            bad += 1
            print(f'FAIL {group}: {name}\n{detail}')

    with tempfile.TemporaryDirectory() as d:
        os.mkdir(os.path.join(d, 'lane'))
        lane = Repo(os.path.join(d, 'lane'), BASE)
        for name, files, labels, passes, text in LANE:
            code, out = lane.check('check_lane.py', files, labels)
            report((code == 0) == passes and text in out, 'check_lane', name, out)
        os.mkdir(os.path.join(d, 'frozen'))
        frozen = Repo(os.path.join(d, 'frozen'), {**BASE, **FREEZE})
        for name, files, passes, text in FROZEN:
            code, out = frozen.check('check_frozen.py', files)
            report((code == 0) == passes and text in out, 'check_frozen', name, out)
        code, out = lane.check('check_frozen.py', {'hotels/index.html': PAGE.replace('Old', 'New')})
        report(code == 0 and 'nothing is frozen' in out, 'check_frozen', 'empty list', out)
        r = run(sys.executable, os.path.join(TOOLS, 'check_lane.py'), '--event', os.path.join(d, 'missing.json'), cwd=lane.path)
        report(r.returncode == 2, 'check_lane', 'no event fails closed', r.stdout + r.stderr)
    for name, pulls, checks, main_commit, want in SHIP:
        got = decide(REPO, SHA, pulls, checks, main_commit, GATE_AT)
        report(got[0] == want, 'ship_check', name, repr(got))
    total = len(LANE) + len(FROZEN) + len(SHIP) + 2
    print(f'test_gate_checks: {"OK" if not bad else "FAILED"}, {total - bad} of {total} cases')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
