#!/usr/bin/env python3
"""Mechanical gate for content/pages/*.json. Prints OK or the list of failures. Exit 1 on any failure.
build-site-pages.py runs it over every page before writing anything, so python3 build.py stops on a failure."""
import json, re, sys, os
ALLOWED = {"p","h2","h3","ul","ol","li","strong","em","a","blockquote","figure","img","figcaption","br"}
LIMITS = {"advisory": (500, 900), "projects": (250, 450), "partners": (400, 700), "guide": (900, 1400), "local": (1100, 1900)}
HYPE = ["elevate", "curated experience", "bespoke journey", "unparalleled", "world-class", "world class", "transform your", "seamlessly", "elevating"]
def words(s): return len(re.sub(r"<[^>]+>", " ", s).split())
def post_slugs():
    """Every Art Radar slug in content/posts.html, for the radar_posts field."""
    try: src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "posts.html"), encoding="utf-8").read()
    except OSError: return set()
    return set(re.findall(r'<article class="post[^"]*" id="([a-z0-9\-]+)">', src))
SLUGS = post_slugs()
def space_keys():
    """The before/after proposal pairs, content/spaces.json (images/spaces/<key>_before.webp and _after.webp)."""
    try: return set(json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "spaces.json"), encoding="utf-8"))["spaces"])
    except (OSError, ValueError, KeyError): return set()
SPACES = space_keys()
def internal_keys(node, trail=""):
    """Key paths holding internal notes, at any depth: editor_note, or a key starting with "_" or "note" (any case).
    Every file under content/ is served publicly, so none of them belongs in a page (content/PAGE-SPEC.md, 2026-09-27)."""
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{trail}.{k}" if trail else k
            if k.lower() == "editor_note" or k.startswith("_") or k.lower().startswith("note"): yield path
            yield from internal_keys(v, path)
    elif isinstance(node, list):
        for i, v in enumerate(node): yield from internal_keys(v, f"{trail}[{i}]")
fails_total = 0
for f in sys.argv[1:]:
    fails = []
    try: p = json.load(open(f, encoding="utf-8"))
    except Exception as e: print(f"{f}: FAIL invalid JSON: {e}"); fails_total += 1; continue
    for k in internal_keys(p): fails.append(f"internal key {k}: remove it. Every file under content/ is public; internal notes, decisions and open questions go to the site owner's private system, never into a page (content/PAGE-SPEC.md)")
    raw = json.dumps(p, ensure_ascii=False)
    if re.search(r"[—–]", raw): fails.append("em/en dash present")
    if re.search(r"\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1[ (]|\b0\d{2}[ -]?\d{7}\b|\+972", raw): fails.append("phone number present")
    if "contact form" in raw.lower(): fails.append("promises a contact form (there is none: say 'the contact details at the end of this page', linking #contact)")
    if p.get("section") == "local":
        for k in ("title_en", "lead_en"):
            if "art curator" not in (p.get(k) or "").lower(): fails.append(f"local page: 'art curator' missing from {k}")
    for slug in p.get("radar_posts", []) or []:
        if slug not in SLUGS: fails.append(f"radar_posts slug does not exist in content/posts.html: {slug}")
    for k in ["path","section","title_en","title_he","meta_description","lead_en","lead_he","body_en","body_he"]:
        if not p.get(k): fails.append(f"missing {k}")
    if p.get("section") not in LIMITS: fails.append("bad section")
    if len(p.get("meta_description","")) > 165: fails.append("meta_description over 165 chars")
    if p.get("section") == "projects" and not p.get("hero_image") and not (p.get("place_en") and p.get("place_he")):
        fails.append("project page without hero_image: give it place_en and place_he (its card shows the place name), or a photo of this project")
    if p.get("section") == "projects" and p.get("before_after"): fails.append("before_after is for article pages: a project page shows only photos of that project")
    if p.get("before_after") and p["before_after"] not in SPACES: fails.append(f"before_after {p['before_after']} is not a key of content/spaces.json")
    for blk in ["body_en","body_he"]:
        tags = set(t.lower() for t in re.findall(r"<\s*([a-zA-Z0-9]+)", p.get(blk,"")))
        bad = tags - ALLOWED
        if bad: fails.append(f"{blk} disallowed tags: {sorted(bad)}")
        for m in re.finditer(r"<img[^>]*>", p.get(blk,"")):
            if 'alt="' not in m.group(0) or 'alt=""' in m.group(0): fails.append(f"{blk} img without alt")
            src = re.search(r'src="([^"]+)"', m.group(0))
            if src and not os.path.exists(src.group(1).lstrip("/")): fails.append(f"{blk} missing image {src.group(1)}")
        if re.search(r'style=|class=|<script', p.get(blk,"")): fails.append(f"{blk} has style/class/script")
    if p.get("section") in LIMITS and p.get("body_en"):
        lo, hi = LIMITS[p["section"]]; n = words(p["body_en"])
        if n < lo or n > hi: fails.append(f"body_en {n} words, expected {lo} to {hi}")
    if p.get("body_he") and words(p["body_he"]) < 0.6 * words(p.get("body_en","")): fails.append("body_he much shorter than body_en, translation incomplete")
    low = p.get("body_en","").lower()
    for h in HYPE:
        if h in low: fails.append(f"hype word: {h}")
    if re.search(r"\$\s?\d|\d+\s?%", p.get("body_en","")) and "industry" not in low: fails.append("numbers with $ or % but no 'industry' labeling")
    for q in p.get("faq", []) or []:
        for k in ["q_en","a_en","q_he","a_he"]:
            if not q.get(k): fails.append(f"faq item missing {k}")
        n = words(q.get("a_en","")); 
        if n and (n < 30 or n > 110): fails.append(f"faq answer {n} words, expected 40 to 90")
    if p.get("hero_image") and not os.path.exists(p["hero_image"]["src"].lstrip("/")): fails.append("hero_image file missing")
    if len(p.get("related", [])) < 2 and p.get("section") != "guide": fails.append("fewer than 2 related pages")
    if fails: print(f"{f}: FAIL\n  - " + "\n  - ".join(fails)); fails_total += 1
    else: print(f"{f}: OK ({words(p['body_en'])} en words)")
sys.exit(1 if fails_total else 0)
