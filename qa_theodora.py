#!/usr/bin/env python3
"""THEODORA SEO QA (from Ron's SEO brief of 2026-09-28, section 5.3). Usage:
  python3 qa_theodora.py .              # check the built site (this repo builds in place: the repo root)
  python3 qa_theodora.py --live         # check the live site via its sitemaps
Prints FAIL lines, a count per check and a summary. Exit code 1 if anything fails.

Adapted to this repo: the site is built in place, so a folder run skips the sources and tooling
that are not pages (content/, templates/, tools/, museum/tools/, .git, .perf, node_modules).
This file is QA tooling, not a page; it holds no secrets. tools/check_site.py lists it in
GATE_FILES because it spells the patterns it hunts."""
import sys, re, json, glob, os, urllib.request

BASE = "https://stavtheodor.com"
PHONE_HREF = 'href="tel:+12013518367"'
GA_SRC = 'async src="https://www.googletagmanager.com/gtag/js?id=G-4300MN0Q97"'
TWO_DECADES_OK = {"/museum/artists/tintoretto/", "/radar/three-tel-aviv-shows/"}  # not about Stav
NEW_PAGES = ["/art-consultant-tenafly-nj/", "/art-advisor-bergen-county/"]
DASH_RE = re.compile(r"\u2014|\u2013|&mdash;|&ndash;|&#8212;|&#8211;|&#x2014;|&#x2013;", re.I)
fails = []

def fail(path, msg):
    fails.append(f"FAIL {path}: {msg}")

def load_pages():
    pages = {}
    if sys.argv[1:] == ["--live"]:
        def get(u):
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 theodora-qa"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        idx = get(BASE + "/sitemap.xml")
        urls = []
        for child in re.findall(r"<loc>([^<]+)</loc>", idx):
            urls += re.findall(r"<loc>([^<]+)</loc>", get(child))
        for extra in ["/designers/"] + NEW_PAGES:
            if BASE + extra not in urls:
                urls.append(BASE + extra)
        for u in urls:
            try:
                pages[u.replace(BASE, "")] = get(u)
            except Exception as e:
                fail(u, f"fetch error {e}")
    else:
        root = sys.argv[1] if sys.argv[1:] else "."
        skip = ("content", "templates", "tools", os.path.join("museum", "tools"), ".git", ".perf", "node_modules")
        for f in glob.glob(os.path.join(root, "**", "*.html"), recursive=True):
            if os.path.relpath(f, root).startswith(tuple(d + os.sep for d in skip)):
                continue
            html = open(f, encoding="utf-8", errors="replace").read()
            m = re.search(r'rel="canonical" href="https://stavtheodor\.com([^"]*)"', html)
            path = m.group(1) if m else "/" + os.path.relpath(f, root)
            pages[path if path not in pages else "/" + os.path.relpath(f, root)] = html
    return pages

def is_stub(html):
    return 'http-equiv="refresh"' in html

def walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values():
            walk(v, fn)
    elif isinstance(node, list):
        for v in node:
            walk(v, fn)

pages = load_pages()
for path, html in sorted(pages.items()):
    if "404" in path:
        continue
    museum = path.startswith("/museum/")
    stub = is_stub(html)
    low = html.lower()
    # 1. dashes (ignore href and src values)
    scrub = re.sub(r'(href|src|srcset)="[^"]*"', "", html)
    if DASH_RE.search(scrub):
        fail(path, f"{len(DASH_RE.findall(scrub))} em/en dash(es)")
    # 2. accuracy strings
    if "two decades" in low and path not in TWO_DECADES_OK:
        fail(path, "'two decades' present")
    if re.search(r"\bcertified\b", low) or "מוסמכת" in html:
        fail(path, "'certified' claim present")
    if "based in new york city and new jersey" in low:
        fail(path, "old FAQ 'based in New York City and New Jersey'")
    if "demott" in low or "41 franklin" in low:
        fail(path, "street address text present")
    # 3. museum links from main pages
    if not museum and re.search(r'href="(https://stavtheodor\.com)?/museum/|href="#museum"', html):
        fail(path, "links to the museum section")
    if stub:
        continue
    # 4. phone, GA, canonical, robots
    if PHONE_HREF not in html:
        fail(path, "no click-to-call tel:+12013518367 link")
    if html.count(GA_SRC) != 1:
        fail(path, f"GA async snippet count = {html.count(GA_SRC)} (want 1)")
    if len(re.findall(r"gtag\('config',\s*'G-4300MN0Q97'\)", html)) != 1:
        fail(path, "gtag config count != 1")
    if "document.head.appendChild(s)" in html:
        fail(path, "deferred GA loader is back")
    if re.search(r'<meta[^>]+name="robots"[^>]+noindex', html, re.I):
        fail(path, "noindex on an indexable page")
    if f'rel="canonical" href="{BASE}{path}"' not in html:
        fail(path, "canonical is not self-referencing")
    # 5. JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if len(blocks) != 1:
        fail(path, f"{len(blocks)} JSON-LD blocks (want exactly 1)")
    orgs = []
    for b in blocks:
        try:
            data = json.loads(b)
        except Exception as e:
            fail(path, f"JSON-LD does not parse: {e}")
            continue
        def check(n):
            t = n.get("@type")
            types = t if isinstance(t, list) else [t]
            biz = any(x in ("ProfessionalService", "LocalBusiness", "Organization", "Person") for x in types)
            if any(x in ("ProfessionalService", "LocalBusiness") for x in types) and len(n) > 3:
                orgs.append(n)  # a full definition, not an {"@id"} reference
            if "areaServed" in n and re.search(r"tel aviv|israel|\"IL\"", json.dumps(n["areaServed"]), re.I):
                fail(path, "Tel Aviv / Israel in areaServed")
            if biz and "streetAddress" in json.dumps(n.get("address", {})):
                fail(path, "streetAddress on THEODORA or Stav (event venues are fine)")
            for s in n.get("sameAs", []) if isinstance(n.get("sameAs"), list) else []:
                if "facebook.com/stavtheodor" in s or "stav-theodor-5542a476" in s:
                    fail(path, f"old sameAs URL {s}")
        walk(data, check)
    if not museum:
        if len(orgs) != 1:
            fail(path, f"{len(orgs)} full ProfessionalService definitions (want 1; reference it elsewhere by @id only)")
        for o in orgs:
            if o.get("telephone") != "+1-201-351-8367":
                fail(path, "ProfessionalService telephone missing or wrong")

# 6. page-level checks
for p in NEW_PAGES:
    if p not in pages:
        fail(p, "new page missing")
d = pages.get("/designers/") or next((h for k, h in pages.items() if k.endswith("designers/index.html") and "for-designers" not in k), None)
if d is not None and not re.search(r'url=https://stavtheodor\.com/for-designers/', d):
    fail("/designers/", "is not a redirect to /for-designers/")

fails = list(dict.fromkeys(fails))
for line in fails:
    print(line)
by_check = {}
for line in fails:
    key = re.sub(r"\d+", "N", line.split(": ", 1)[1])
    key = re.sub(r"old sameAs URL .*", "old sameAs URL", key)
    by_check[key] = by_check.get(key, 0) + 1
if by_check:
    print("\nFailures per check:")
    for key, n in sorted(by_check.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {key}")
print(f"\nChecked {len(pages)} pages. {len(fails)} failure(s).")
sys.exit(1 if fails else 0)
