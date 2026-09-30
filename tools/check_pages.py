#!/usr/bin/env python3
"""Mechanical gate for content/pages/*.json. Prints OK or the list of failures. Exit 1 on any failure.
build-site-pages.py runs it over every page before writing anything, so python3 build.py stops on a failure."""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fee_gate import fee_violation  # the fee rule, 2026-09-29
ALLOWED = {"p","h2","h3","ul","ol","li","strong","em","a","blockquote","figure","img","figcaption","br"}
# A guide's body may also carry the guide components (Fable's design spec, 2026-09-29, content/PAGE-SPEC.md): figure.dia,
# figure.tbl with div.tbl-x and the table, aside.cnote with span.cn-l, div.keynums of div.keynum (span.n, span.l, small),
# and class attributes from GUIDE_CLASSES only. Every other page keeps ALLOWED and no class at all.
GUIDE_TAGS = {"div","span","small","aside","table","thead","tbody","tr","th","td"}
GUIDE_CLASSES = {"dia","fig-n","cnote","cn-l","keynums","keynum","n","l","tbl","tbl-x"}
GUIDE_PATH = re.compile(r"^guide/[a-z0-9]+(?:-[a-z0-9]+)*$")
GUIDES_COUNT = (1, 6)
# (field, max characters): the card's line, the breadcrumb's short name, the guides strip's heading, Read next's h2
FIELD_MAX = {"dek_en": 120, "dek_he": 120, "crumb_en": 40, "crumb_he": 40, "guides_heading_en": 90, "guides_heading_he": 90,
             "readnext_h2_en": 90, "readnext_h2_he": 90}
# partners up to 1000 since 2026-09-29: /designers/ was merged into /for-designers/ (Ron's SEO brief, P1.5)
# area: the town and county pages (Ron's SEO brief, 2026-09-29, P1.2 and P1.3), 700 to 1,200 English words counted over the
# lead, the body and the questions, with the brief's own short answers (FAQ_AREA)
LIMITS = {"advisory": (500, 900), "projects": (250, 450), "partners": (400, 1000), "guide": (900, 1400), "local": (1100, 1900), "area": (700, 1200)}
FAQ_WORDS = (30, 110)
FAQ_AREA = (10, 110)
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
def guide_pages():
    """{path: page} for every content/pages JSON of section guide, for the guides field."""
    out = {}
    for g in sorted(os.listdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "pages"))):
        if g.endswith(".json"):
            try: d = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content", "pages", g), encoding="utf-8"))
            except (OSError, ValueError): continue
            if isinstance(d, dict) and d.get("section") == "guide" and isinstance(d.get("path"), str): out[d["path"].strip("/")] = d
    return out
GUIDES = guide_pages()
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
    if p.get("section") == "local":  # the h1 may lead with "art consultant" since 2026-09-29 (Ron's SEO brief, P1.4); the lead keeps "art curator"
        if not re.search(r"art (curator|consultant|advisor)", (p.get("title_en") or "").lower()): fails.append("local page: 'art curator', 'art consultant' or 'art advisor' missing from title_en")
        if "art curator" not in (p.get("lead_en") or "").lower(): fails.append("local page: 'art curator' missing from lead_en")
    if p.get("section") == "area":  # the head term in the h1, the town or county in the h1 and the lead, the brief's schema fields
        if not re.search(r"art (consultant|advisor)", (p.get("title_en") or "").lower()): fails.append("area page: 'art consultant' or 'art advisor' missing from title_en")
        for k in ("breadcrumb", "service", "og_title"):
            if not p.get(k): fails.append(f"area page: missing {k}")
        crumbs = p.get("breadcrumb") or []
        if crumbs and (crumbs[0][2] != "/" or crumbs[-1][2] != "/" + p.get("path", "").strip("/") + "/"): fails.append("area page: breadcrumb must run from / to the page itself")
        for k in ("name", "serviceType", "areaServed", "description"):
            if not (p.get("service") or {}).get(k): fails.append(f"area page: service.{k} missing")
    if bool(p.get("nav_sub_en")) != bool(p.get("nav_sub_he")): fails.append("nav_sub_en and nav_sub_he come together (the line under the wordmark, both languages)")
    for k in ("nav_sub_en", "nav_sub_he"):
        if p.get(k) and len(p[k]) > 32: fails.append(f"{k}: at most 32 characters")
    if p.get("head_title") and (len(p["head_title"]) + len(" · THEODORA") > 60): fails.append("head_title: the title with ' · THEODORA' is over 60 characters")
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
    guide = p.get("section") == "guide"
    for blk in ["body_en","body_he"]:
        tags = set(t.lower() for t in re.findall(r"<\s*([a-zA-Z0-9]+)", p.get(blk,"")))
        bad = tags - ALLOWED - (GUIDE_TAGS if guide else set())
        if bad: fails.append(f"{blk} disallowed tags: {sorted(bad)}")
        for m in re.finditer(r"<img[^>]*>", p.get(blk,"")):
            if 'alt="' not in m.group(0) or 'alt=""' in m.group(0): fails.append(f"{blk} img without alt")
            src = re.search(r'src="([^"]+)"', m.group(0))
            if src and not os.path.exists(src.group(1).lstrip("/")): fails.append(f"{blk} missing image {src.group(1)}")
        if re.search(r'style=|<script', p.get(blk,"")) or (not guide and "class=" in p.get(blk,"")): fails.append(f"{blk} has style/class/script")
        if guide:
            for cls in re.findall(r'class="([^"]*)"', p.get(blk,"")):
                off = [c for c in cls.split() if c not in GUIDE_CLASSES]
                if off: fails.append(f"{blk} class not allowed on a guide: {off} (allowed: {', '.join(sorted(GUIDE_CLASSES))})")
            if re.search(r"class='|class=[^\"']", p.get(blk,"")): fails.append(f"{blk}: write class attributes in double quotes")
    if p.get("section") in LIMITS and p.get("body_en"):
        lo, hi = LIMITS[p["section"]]; n = words(p["body_en"])
        if p["section"] == "area": n = words(p["lead_en"] + " " + p["body_en"] + " " + " ".join(q.get("q_en", "") + " " + q.get("a_en", "") for q in p.get("faq", []) or []))
        if n < lo or n > hi: fails.append(f"body_en {n} words, expected {lo} to {hi}")
    if p.get("body_he") and words(p["body_he"]) < 0.6 * words(p.get("body_en","")): fails.append("body_he much shorter than body_en, translation incomplete")
    low = p.get("body_en","").lower()
    for h in HYPE:
        if h in low: fails.append(f"hype word: {h}")
    # Fee rule (Ron, 2026-09-29; tools/fee_gate.py): Stav's fees are never stated and no page carries a $ figure. A percentage
    # fails only in a sentence with a fee word (fee, commission, retainer, markup, charge, rate, pricing); research statistics stay.
    def strings(node):
        if isinstance(node, str): yield node
        elif isinstance(node, dict):
            for v in node.values(): yield from strings(v)
        elif isinstance(node, list):
            for v in node: yield from strings(v)
    fee = next(filter(None, map(fee_violation, strings(p))), None)
    if fee: fails.append(f"a fee or $ figure ({fee!r}): no dollar figures, and no percentage in a sentence about fees (content/BRIEF.md section 5, tools/fee_gate.py)")
    for q in p.get("faq", []) or []:
        for k in ["q_en","a_en","q_he","a_he"]:
            if not q.get(k): fails.append(f"faq item missing {k}")
        n = words(q.get("a_en","")); lo, hi = FAQ_AREA if p.get("section") == "area" else FAQ_WORDS
        if n and (n < lo or n > hi): fails.append(f"faq answer {n} words, expected {lo} to {hi}")
    if p.get("hero_image") and not os.path.exists(p["hero_image"]["src"].lstrip("/")): fails.append("hero_image file missing")
    for k, n in FIELD_MAX.items():
        if p.get(k) is not None and not (isinstance(p[k], str) and 0 < len(p[k]) <= n): fails.append(f"{k}: a string of 1 to {n} characters")
    for a in ("dek", "crumb", "guides_heading", "readnext_h2"):
        if bool(p.get(a + "_en")) != bool(p.get(a + "_he")): fails.append(f"{a}_en and {a}_he come together (both languages)")
    if "guides" in p:  # the #guides strip (Fable's design, 2026-09-29): 1 to 6 guide pages, in display order
        gs = p["guides"]
        if p.get("section") == "guide": fails.append("guides: a guide links other guides through related (Read next), not guides")
        if not isinstance(gs, list) or not all(isinstance(x, str) for x in gs): fails.append('guides: a list of "guide/<slug>" paths')
        else:
            if not GUIDES_COUNT[0] <= len(gs) <= GUIDES_COUNT[1]: fails.append(f"guides: {len(gs)} entries, expected {GUIDES_COUNT[0]} to {GUIDES_COUNT[1]}")
            if len(set(gs)) != len(gs): fails.append("guides: an entry appears twice")
            for x in gs:
                if not GUIDE_PATH.match(x): fails.append(f'guides: "{x}" is not a guide path ("guide/<slug>", no slashes around it)')
                elif x not in GUIDES: fails.append(f'guides: "{x}" is not a guide page in content/pages')
                elif not (GUIDES[x].get("hero_image") or GUIDES[x].get("before_after")): fails.append(f'guides: "{x}" has neither a hero_image nor a before_after, so it has no card')
    elif "guides_heading_en" in p: fails.append("guides_heading_en: only beside guides")
    if len(p.get("related", [])) < 2 and p.get("section") != "guide": fails.append("fewer than 2 related pages")
    if fails: print(f"{f}: FAIL\n  - " + "\n  - ".join(fails)); fails_total += 1
    else: print(f"{f}: OK ({words(p['body_en'])} en words)")
sys.exit(1 if fails_total else 0)
