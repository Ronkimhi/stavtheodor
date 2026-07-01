#!/usr/bin/env python3
"""
validate_data.py — sanity checks on museum/data/ before committing.

Checks schema completeness, per-period artist counts, and (with --urls)
HEAD-checks every image URL against Wikimedia.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CHECK_URLS = "--urls" in sys.argv
UA = "TheodoraMuseumBot/1.0 (https://stavtheodor.com; ronkkimhi@gmail.com)"

errors, warnings = [], []


def head_ok(url):
    # retry once after a pause: bulk sweeps can trip transient rate limiting
    for attempt in range(2):
        r = subprocess.run(
            ["curl", "-sI", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "30", "-A", UA, url],
            capture_output=True, text=True,
        )
        if r.stdout.strip() == "200":
            return True
        time.sleep(3)
    return False


index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
periods = {p["id"]: p for p in index["periods"]}

for p in index["periods"]:
    for k in ("id", "name", "start", "end", "lane", "summary", "source"):
        if p.get(k) in (None, ""):
            errors.append(f"period {p.get('id')}: missing {k}")

per_period = {pid: 0 for pid in periods}
for a in index["artists"]:
    for pid in a["periods"]:
        if pid not in periods:
            errors.append(f"artist {a['slug']}: unknown period {pid}")
        else:
            per_period[pid] += 1

for pid, n in per_period.items():
    if n < 3:
        errors.append(f"period {pid}: only {n} artists (need 3+)")

gallery_count = 0
url_checked = url_bad = 0
for a in index["artists"]:
    f = DATA / "artists" / f"{a['slug']}.json"
    if not f.exists():
        errors.append(f"missing artist file: {a['slug']}.json")
        continue
    full = json.loads(f.read_text(encoding="utf-8"))
    if not full["bio"]["extract"]:
        warnings.append(f"{a['slug']}: empty bio")
    if full["hasGallery"]:
        gallery_count += 1
        if len(full["paintings"]) < 6:
            errors.append(f"{a['slug']}: hasGallery but only {len(full['paintings'])} paintings")
        if len(full["paintings"]) < 8:
            warnings.append(f"{a['slug']}: below preferred 8 paintings ({len(full['paintings'])})")
    for p in full["paintings"]:
        for k in ("thumb640", "thumb1600"):
            if not p["image"].get(k):
                errors.append(f"{a['slug']} / {p['title']}: missing {k}")
        lic = (p.get("license", {}).get("name") or "").lower()
        if not any(x in lic for x in ("public domain", "pd", "cc0", "no restrictions")):
            errors.append(f"{a['slug']} / {p['title']}: suspect license '{lic}'")
        if CHECK_URLS:
            for k in ("thumb640", "thumb1600"):
                u = p["image"].get(k)
                if u:
                    url_checked += 1
                    if not head_ok(u):
                        url_bad += 1
                        errors.append(f"{a['slug']} / {p['title']}: {k} not 200")
                    time.sleep(0.15)

print(f"periods: {len(periods)}  artists: {len(index['artists'])}  galleries: {gallery_count}")
if CHECK_URLS:
    print(f"image URLs checked: {url_checked}, failing: {url_bad}")
for w in warnings:
    print("WARN:", w)
for e in errors:
    print("ERROR:", e)
print("RESULT:", "FAIL" if errors else "OK")
sys.exit(1 if errors else 0)
