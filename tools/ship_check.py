#!/usr/bin/env python3
"""Decides whether ship.yml may merge the PR behind a finished gate run. Merges nothing, reads JSON only.

    python3 tools/ship_check.py --repo OWNER/NAME --sha HEAD_SHA --gate-created ISO_TIME \\
        --pulls commits_sha_pulls.json --checks gate_check_runs.json --main main_commit.json

Prints the reason, and writes decision=ship|stale|skip and number=N to $GITHUB_OUTPUT when that is set.
  ship   an open, ready PR from this repo into main, labelled auto-ship, whose head is this commit, with gate green
         on it and main unchanged since the gate started
  stale  all of that, but main moved after the gate started, so the gate never tested this merge
  skip   anything else
Self test: tools/test_gate_checks.py
"""
import argparse
import json
import os
from datetime import datetime

LABEL = 'auto-ship'
BASE = 'main'


def when(iso):
    return datetime.fromisoformat(iso.replace('Z', '+00:00'))


def decide(repo, sha, pulls, checks, main_commit, gate_created):
    """(decision, PR number or None, reason)."""
    mine = [p for p in pulls if p.get('state') == 'open' and p['head']['sha'] == sha]
    if len(mine) != 1:
        return 'skip', None, f'{len(mine)} open PRs have {sha} as their head, expected 1'
    pr = mine[0]
    number = pr['number']
    if pr.get('draft') is not False:
        return 'skip', number, 'draft'
    if LABEL not in {label['name'] for label in pr['labels']}:
        return 'skip', number, f'no {LABEL} label'
    if (pr['head'].get('repo') or {}).get('full_name') != repo:
        return 'skip', number, 'from a fork'
    if pr['base']['ref'] != BASE:
        return 'skip', number, f'base is {pr["base"]["ref"]}, not {BASE}'
    runs = checks.get('check_runs', [])
    if not runs or any(r.get('conclusion') != 'success' for r in runs):
        return 'skip', number, 'gate is not green on this commit'
    if when(main_commit['commit']['committer']['date']) > when(gate_created):
        return 'stale', number, f'{BASE} moved after this gate run started'
    return 'ship', number, 'gate is green and every rule holds'


def main():
    ap = argparse.ArgumentParser()
    for name in ('repo', 'sha', 'gate-created', 'pulls', 'checks', 'main'):
        ap.add_argument('--' + name, required=True)
    a = ap.parse_args()
    read = lambda p: json.load(open(p, encoding='utf-8'))
    decision, number, reason = decide(a.repo, a.sha, read(a.pulls), read(a.checks), read(a.main), a.gate_created)
    print(f'ship_check: {decision}, PR {number}: {reason}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as out:
            out.write(f'decision={decision}\nnumber={number or ""}\n')


if __name__ == '__main__':
    main()
