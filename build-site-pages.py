#!/usr/bin/env python3
"""
Renders content/pages/*.json into standalone bilingual pages at /<path>/index.html
(advisory, projects, partners, guide, the two local landing pages and the town and county pages), plus the hub pages
/advisory/ and /projects/,
in the site's one theme (css/theme.css) with the shared chrome (site_chrome.py).
Every page must first pass tools/check_pages.py; a failure stops the build before anything is written.
Then runs build-post-pages.py (radar/<slug>/ and the archive). The sitemaps are
written afterwards by tools/build_sitemap.py.
Idempotent. Run from the repo root, or just run python3 build.py.
"""
import glob, json, os, re, sys, html as H, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_chrome as sc
from site_chrome import SITE, T

KICKER_HE = {
    "Art advisory": "ייעוץ אמנות", "Project": "פרויקט", "Working together": "עבודה משותפת",
    "Guide": "מדריך", "For partners": "לשותפים", "THEODORA": "THEODORA",
    'Private residence': 'בית פרטי',
    'Private residence, Tel Aviv': 'בית פרטי, תל אביב',
    'Bauhaus residence, Tel Aviv': 'בית באוהאוס, תל אביב',
    'Private residence, Closter, New Jersey': "בית פרטי, קלוסטר, ניו ג'רזי",
    'Hospitality': 'אירוח',
    'Private villa, Hod Hasharon': 'וילה פרטית, הוד השרון',
    'Renovated Bauhaus home, Tel Aviv': 'בית באוהאוס משופץ, תל אביב',
    'Exhibition': 'תערוכה',
    'Private residence, Manhattan': 'בית פרטי, מנהטן',
    'Sea view villa, Caesarea': 'וילה עם נוף לים, קיסריה',
}
SECTION_KICKER = {"advisory": "Art advisory", "projects": "Project", "partners": "Working together", "guide": "Guide", "local": "Art curator"}
SECTION_KICKER_HE = {"advisory": "ייעוץ אמנות", "projects": "פרויקט", "partners": "עבודה משותפת", "guide": "מדריך", "local": "אוצרת אמנות"}
# Breadcrumb parents. The two local landing pages (/art-curator-new-jersey/, /art-curator-new-york/,
# section "local", added 2026-09-26) sit under /advisory/ in the breadcrumb and open the advisory hub.
# The guides sit under /advisory/ too since 2026-09-29 (Fable's guide design): the visible trail reads Home, Advisory, the
# guide, and the BreadcrumbList THEODORA, Advisory, the guide.
CRUMB_NAME = {"advisory": "Advisory", "local": "Advisory", "projects": "Projects", "partners": "Working together", "guide": "Advisory"}
CRUMB_DIR = {"advisory": "advisory", "local": "advisory", "projects": "projects", "guide": "advisory"}
# The service area in every Service block (Ron's SEO brief, 2026-09-29): the entity's own areaServed. Tel Aviv
# stays in the copy and on the project pages but never in an areaServed.
DEFAULT_AREA = [{"@type": "City", "name": "Tenafly, New Jersey"}, {"@type": "AdministrativeArea", "name": "Bergen County, New Jersey"},
                {"@type": "State", "name": "New Jersey"}, {"@type": "City", "name": "New York City"}]
# The town and county pages (section "area": /art-consultant-tenafly-nj/ and /art-advisor-bergen-county/, Ron's SEO brief,
# 2026-09-29, P1.2 and P1.3). Their JSON carries its own schema and path: `breadcrumb` (the visible trail and the
# BreadcrumbList, [name_en, name_he, path] per step, the page itself last), `service` (the Service node: name,
# serviceType, areaServed, audience, description) and `og_title`; `cta_sub_en`/`cta_sub_he` add a line under the CTA,
# which also links /contact/. The FAQPage carries an @id, and its answers are the visible text, tags stripped.
CTA_EN = "Send me one photo of the wall, and a line about the space. I will tell you what I see."
CTA_HE = "שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה."
MAIL = f"mailto:{sc.EMAIL}"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def lazy_images(body):
    """The reading column's figures sit below the fold: lazy and async unless the JSON says otherwise
    (2026-09-26, speed pass). The hero image above the text stays eager."""
    return re.sub(r'<img(?![^>]*\bloading=)([^>]*?)\s*/?>', r'<img\1 loading="lazy" decoding="async">', body or '')


def snippet(s, n=165):
    """Short Hebrew card blurb. The JSON carries no Hebrew meta_description, so the
    Hebrew lead is trimmed at a sentence or word boundary instead."""
    t = strip_tags(s)
    if len(t) <= n:
        return t
    cut = t[:n]
    for sep in (". ", "? ", "! "):
        i = cut.rfind(sep)
        if i > n * 0.5:
            return cut[:i + 1]
    i = cut.rfind(" ")
    return (cut[:i] if i > 0 else cut).rstrip(",;:") + "..."


def load_pages():
    pages = []
    for f in sorted(glob.glob("content/pages/*.json")):
        p = json.load(open(f, encoding="utf-8"))
        p["_file"] = f
        p["slug"] = p["path"].strip("/").split("/")[-1]
        pages.append(p)
    return pages


def kickers(p):
    kicker = p.get("kicker", SECTION_KICKER.get(p["section"], "THEODORA"))
    kicker_he = p.get("kicker_he", KICKER_HE.get(kicker, SECTION_KICKER_HE.get(p["section"], "THEODORA")))
    return kicker, kicker_he


def ld_area(p, url):
    """A town or county page: its Service, its BreadcrumbList and its FAQPage, as the brief writes them."""
    sv = p["service"]
    service = {"@type": "Service", "@id": url + "#service", "name": sv["name"], "serviceType": sv["serviceType"], "url": url,
               "provider": {"@id": SITE + "/#org"}, "areaServed": sv["areaServed"]}
    if sv.get("audience"):
        service["audience"] = sv["audience"]
    service["description"] = sv["description"]
    crumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": en, "item": SITE + path} for i, (en, _he, path) in enumerate(p["breadcrumb"])]}
    ld = [service, crumbs]
    if p.get("faq"):
        ld.append({"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": q["q_en"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(q["a_en"])}} for q in p["faq"]]})
    return ld


def crumbs_html(p):
    """The visible breadcrumb of a town or county page, in place of the eyebrow: every step but the last is a link."""
    steps = []
    for i, (en, he, path) in enumerate(p["breadcrumb"]):
        label = T(H.escape(en), H.escape(he))
        steps.append(f'<a href="{path}">{label}</a>' if i < len(p["breadcrumb"]) - 1 else f'<span aria-current="page">{label}</span>')
    sep = ' <span class="sep" aria-hidden="true">/</span> '
    return f'<nav class="eyebrow crumbs" aria-label="Breadcrumb">{sep.join(steps)}</nav>'


def ld_blocks(p, url, og):
    if p["section"] == "area":
        return ld_area(p, url)
    date = p.get("date", "2026-09-04")
    main = {
        "@context": "https://schema.org",
        "@type": p.get("schema_type", "WebPage"),
        "name": p["title_en"], "headline": p["title_en"],
        "description": p["meta_description"],
        "url": url, "mainEntityOfPage": url,
        "inLanguage": ["en", "he"],
        "datePublished": date, "dateModified": p.get("date_modified", date),
        "image": og,
        # Stav and THEODORA are defined once per page, in the site-wide nodes (content/entity.json); here by @id only
        "author": {"@id": SITE + "/#stav"},
        "publisher": {"@id": SITE + "/#org"},
    }
    if p.get("schema_type") == "Service":
        # provider is the entity itself (content/entity.json, @id #org, on every page), by reference only
        main.update({"provider": {"@id": SITE + "/#org"},
                     "areaServed": p.get("area_served") or DEFAULT_AREA, "serviceType": p.get("service_type", "Art advisory")})
    if p["section"] == "guide":  # the byline's author: the site-wide Person (same @id, so one Stav), with the about page and Instagram
        main["author"] = {"@type": "Person", "@id": SITE + "/#stav", "name": "Stav Theodor", "url": SITE + "/about/",
                          "sameAs": [sc.INSTAGRAM]}
    main.update(p.get("schema_extra", {}))
    crumbs = [{"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"}]
    if p["section"] in CRUMB_DIR:  # sections with a hub page get a middle crumb (the guides: Advisory); partners go straight to the page
        crumbs.append({"@type": "ListItem", "position": 2, "name": CRUMB_NAME[p["section"]], "item": SITE + "/" + CRUMB_DIR[p["section"]] + "/"})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": p["title_en"], "item": url})
    ld = [main, {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}]
    if p.get("faq"):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "en",
                   "mainEntity": [{"@type": "Question", "name": q["q_en"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(q["a_en"])}} for q in p["faq"]]})
    return ld


def faq_html(p, cls=""):
    """The questions; cls "guide-faq" on a guide (the question a size smaller, design spec 2.8)."""
    if not p.get("faq"):
        return ""
    qas = "".join(f'''
      <details class="qa">
        <summary><h3 class="serif">{T(H.escape(q["q_en"]), H.escape(q["q_he"]))}</h3><span class="plus" aria-hidden="true"></span></summary>
        <p class="body">{T(q["a_en"], q["a_he"])}</p>
      </details>''' for q in p["faq"])
    return f'''
<section class="section wrap{(" " + cls) if cls else ""}">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('Questions', 'שאלות')}</p><h2 class="serif">{T('Questions people ask', 'שאלות נפוצות')}</h2></div></div>
  <div class="qas reveal">{qas}
  </div>
</section>
'''


def related_html(p, all_pages, exclude_projects=False):
    rel = [r for r in p.get("related", []) if any(o["path"].strip("/") == r.strip("/") for o in all_pages)]
    if exclude_projects:
        rel = [r for r in rel if not r.strip("/").startswith("projects/")]
    if not rel:
        return ""
    links = []
    for r in rel:
        o = next(o for o in all_pages if o["path"].strip("/") == r.strip("/"))
        links.append(f'<a href="/{o["path"].strip("/")}/">{T(H.escape(o["title_en"]), H.escape(o.get("title_he") or o["title_en"]))}</a>')
    return f'<div class="readnext"><p class="eyebrow soft" style="margin-top: 24px;">{T("Read next", "להמשך קריאה")}</p>{"".join(links)}</div>'


_posts_cache = None


def posts():
    """Every Art Radar post, newest first, read once per build."""
    global _posts_cache
    if _posts_cache is None:
        _, _posts_cache = sc.read_posts()
    return _posts_cache


def radar_html(p):
    """From Art Radar, on every article page: the posts named in radar_posts (in that order),
    or the three newest. Same timeline markup as the homepage and the post pages."""
    by = {q["slug"]: q for q in posts()}
    chosen = [by[s] for s in p.get("radar_posts") or [] if s in by] or posts()[:3]
    return f'''
<section class="section wrap tight">
  <div class="head reveal">
    <div class="lead"><p class="eyebrow">{T('From Art Radar', 'מראדאר אמנות')}</p><h2 class="serif">{T('The art worth seeing, chosen by a curator.', 'האמנות ששווה לראות, בבחירת אוצרת.')}</h2></div>
    <a class="arrow" href="/radar/"><span class="ln"></span>{T('All posts', 'כל הפוסטים')}</a>
  </div>
  <div class="timeline">{sc.timeline(chosen, with_months=False)}
  </div>
</section>
'''


def cta_html(p):
    cta_en = p.get("cta_en") or CTA_EN
    cta_he = p.get("cta_he") or CTA_HE
    sub = ""
    if p.get("cta_sub_en"):
        sub = f'\n    <p class="muted">{T(p["cta_sub_en"], p["cta_sub_he"])}</p>'
    contact = ""
    if p["section"] == "area":
        contact = f'\n    <a class="arrow" href="/contact/"><span class="ln"></span>{T("All the ways to reach me", "כל הדרכים ליצור איתי קשר")}</a>'
    return f'''
  <div class="cta reveal">
    <h2 class="serif">{T(cta_en, cta_he)}</h2>{sub}
    <a class="btn" href="{MAIL}">{T('Write to Stav', 'כתבו לסתיו')}</a>
    {sc.phone_link('cta')}{contact}
  </div>'''


# ---------------------------------------------------------------- the guides (Fable's design spec, 2026-09-29)
# A guide page (section "guide"): breadcrumb Home / Advisory / the guide, a tighter h1, the hero diagram as Figure 1, the
# reading column as .prose.guide (text at 720px, figures and tables to 1000px), numbered figures and tables, h2 ids,
# then Questions, the CTA, Read next as cards and links, and From Art Radar last. Body components (content/PAGE-SPEC.md):
# figure.dia (a diagram img plus figcaption), figure.tbl (figcaption plus div.tbl-x holding the table), aside.cnote
# (span.cn-l plus p), div.keynums of div.keynum (span.n, span.l). The build numbers the captions (Figure N / תרשים N,
# Table N / טבלה N; the JSON may leave the number out), adds width and height to diagram imgs from the SVG, and ids to
# every h2 (slug of the English text; the Hebrew twin's h2 takes the same id plus "-he").
FIG_LABEL = {("dia", "en"): "Figure", ("dia", "he"): "תרשים", ("tbl", "en"): "Table", ("tbl", "he"): "טבלה"}
FIGURE_RE = re.compile(r'<figure class="(dia|tbl)">(.*?)</figure>', re.S)
# The /advisory/ hub's guides group, in this order (slugs, like PROJECT_ORDER); guides not listed follow, newest first.
GUIDE_ORDER = ["gallery-wall-ideas", "how-to-hang-pictures", "art-above-couch", "dining-room-art", "living-room-art",
               "art-above-bed", "entryway-art", "large-wall-art-ideas"]  # the eight home guides, 2026-09-30 (Commit B)
GUIDES_HUB_H2 = ("Practical guides to choosing and placing art", "מדריכים מעשיים לבחירת אמנות ולמיקומה")
GUIDES_HUB_SUB = ("Each guide answers one question with drawings to scale and the measurements in inches and centimeters.",
                  "כל מדריך עונה על שאלה אחת, עם שרטוטים בקנה מידה והמידות באינצ'ים ובסנטימטרים.")


def number_figures(body, lang, fig_start):
    """Number every diagram figure (from fig_start: the hero diagram is Figure 1) and every table (from 1) in reading order,
    in both twins alike, and give each diagram img its width and height from the SVG when the JSON does not."""
    n = {"dia": fig_start, "tbl": 1}

    def one(m):
        kind, inner = m.group(1), m.group(2)
        num = n[kind]
        n[kind] += 1
        label = f'<span class="fig-n">{FIG_LABEL[kind, lang]} {num}</span>'

        def cap(c):
            text = re.sub(r'<span class="fig-n">.*?</span>', '', c.group(1), flags=re.S).strip()
            if text and not re.fullmatch(r'<span>(?:(?!</?span\b).)*</span>', text, re.S):
                text = f'<span>{text}</span>'
            return f'<figcaption>{label}{text}</figcaption>'
        inner, k = re.subn(r'<figcaption>(.*?)</figcaption>', cap, inner, count=1, flags=re.S)
        if not k:
            inner = (inner.rstrip() + f'\n  <figcaption>{label}</figcaption>\n') if kind == "dia" else f'<figcaption>{label}</figcaption>' + inner
        if kind == "dia":
            def dims(im):
                tag = im.group(0)
                src = re.search(r'\ssrc="([^"]+)"', tag)
                d = src and not re.search(r'\swidth=', tag) and sc.svg_dims(src.group(1))
                return re.sub(r'\s*/?>$', f' width="{d[0]}" height="{d[1]}">', tag) if d else tag
            inner = re.sub(r'<img\b[^>]*>', dims, inner)
        return f'<figure class="{kind}">{inner}</figure>'
    return FIGURE_RE.sub(one, body or "")


def h2_ids(body_en, body_he):
    """Every h2 gets an id: the slug of its English text (ASCII, hyphens), kept if the JSON set one; the Hebrew twin's
    h2 in the same position gets the same id plus "-he", so ids stay unique on the page."""
    ids, seen = [], set()

    def en(m):
        attrs, inner = m.group(1), m.group(2)
        own = re.search(r'\sid="([^"]+)"', attrs)
        base = own.group(1) if own else (re.sub(r"[^a-z0-9]+", "-", strip_tags(inner).lower()).strip("-") or "section")
        i, k = base, 2
        while i in seen:
            i, k = f"{base}-{k}", k + 1
        seen.add(i)
        ids.append(i)
        rest = re.sub(r'\sid="[^"]*"', "", attrs)
        return m.group(0) if own and i == base else f'<h2 id="{i}"{rest}>{inner}</h2>'
    body_en = re.sub(r"<h2\b([^>]*)>(.*?)</h2>", en, body_en, flags=re.S)
    pos = iter(range(10 ** 6))

    def he(m):
        attrs, inner = m.group(1), m.group(2)
        k = next(pos)
        if re.search(r'\sid="', attrs):
            return m.group(0)
        return f'<h2 id="{(ids[k] if k < len(ids) else f"section-{k + 1}")}-he"{attrs}>{inner}</h2>'
    body_he = re.sub(r"<h2\b([^>]*)>(.*?)</h2>", he, body_he, flags=re.S)
    return body_en, body_he


def guide_crumbs(p):
    """The visible trail of a guide, in place of the eyebrow: Home / Advisory / the guide (crumb_en or the title,
    clipped to one line by CSS and hidden on a phone, where the h1 sits right under it)."""
    sep = '<span class="sep" aria-hidden="true">/</span>'
    cur = T(H.escape(p.get("crumb_en") or p["title_en"]), H.escape(p.get("crumb_he") or p["title_he"]))
    return (f'<nav class="eyebrow crumbs" aria-label="Breadcrumb"><a href="/">{T("Home", "דף הבית")}</a> {sep} '
            f'<a href="/advisory/">{T("Art advisory", "ייעוץ אמנות")}</a> {sep} <span class="cur" aria-current="page">{cur}</span></nav>')


BYLINE_DEFAULT = ("By Stav Theodor, art curator and advisor at THEODORA in Tenafly, New Jersey",
                  "מאת סתיו תאודור, אוצרת ויועצת אמנות ב-THEODORA בטנפליי, ניו ג'רזי")
BYLINE_NAME = ("Stav Theodor", "סתיו תאודור")  # linked to /about/ where it appears in the line


def guide_byline(p):
    """The visible byline under a guide's lead (Curator microcopy 2026-09-29): byline_en/_he, else the default line;
    the name in it links to /about/. Small caps in muted ink, the site's eyebrow style."""
    def one(text, name):
        t = H.escape(text)
        n = H.escape(name)
        return t.replace(n, f'<a href="/about/">{n}</a>', 1) if n in t else t
    en, he = p.get("byline_en") or BYLINE_DEFAULT[0], p.get("byline_he") or BYLINE_DEFAULT[1]
    return f'\n  <p class="eyebrow soft byline">{T(one(en, BYLINE_NAME[0]), one(he, BYLINE_NAME[1]))}</p>'


def built_pages(all_pages):
    """{path: page} for every page this build writes (it passes check()), for the guides fields."""
    return {o["path"].strip("/"): o for o in all_pages if not check(o, "")}


def guide_next(p, all_pages):
    """Read next on a guide: its related guides as cards (at most three, in the order listed) under a head with the
    "All guides" arrow, then the other related pages as text links under "Also on this site". Without a related guide,
    only the links, under "Read next", and no head."""
    built = built_pages(all_pages)
    rel = [built[r.strip("/")] for r in p.get("related", []) if r.strip("/") in built]
    guides = [o for o in rel if o["section"] == "guide" and sc.guide_cardable(o)][:3]
    rest = [o for o in rel if o not in guides]
    link = lambda o: f'<a href="/{o["path"].strip("/")}/">{T(H.escape(o["title_en"]), H.escape(o.get("title_he") or o["title_en"]))}</a>'
    if not guides:
        links = related_html(p, all_pages)
        return f'\n<section class="section wrap tight guide-next" id="next">\n  {links}\n</section>\n' if links else ""
    h2 = (H.escape(p.get("readnext_h2_en") or "More guides"), H.escape(p.get("readnext_h2_he") or "עוד מדריכים"))
    arrow = (f'<a class="arrow" href="/advisory/#guides"><span class="ln"></span>{T(*sc.GUIDES_ALL)}</a>'
             if sc.hub_guides(built.values()) else "")
    more = (f'\n  <div class="readnext"><p class="eyebrow soft">{T("Also on this site", "עוד באתר")}</p>{"".join(link(o) for o in rest)}</div>'
            if rest else "")
    return f'''
<section class="section wrap tight guide-next" id="next">
  <div class="head reveal">
    <div class="lead"><p class="eyebrow">{T('Read next', 'להמשך קריאה')}</p><h2 class="serif">{T(*h2)}</h2></div>
    {arrow}
  </div>
  {sc.gcards(guides)}{more}
</section>
'''


def page_guides(p, all_pages):
    """A content page's #guides strip (the page's optional `guides`, 1 to 6 guide paths): after the reading column and
    before the questions. Heading guides_heading_en/_he, else "The answers in more detail"; no arrow, no sub (design spec 3.2)."""
    if p["section"] == "guide" or not p.get("guides"):
        return ""
    built = built_pages(all_pages)
    h2 = (H.escape(p.get("guides_heading_en") or "The answers in more detail"), H.escape(p.get("guides_heading_he") or "התשובות, בפירוט"))
    return sc.guides_section(sc.pick_guides(p["guides"], built, lambda o: True), h2, tight=True) + "\n"


def render_article_page(p, all_pages):
    """Advisory, partner and guide pages: text header, the hero figure, the reading column.
    The hero figure is a before/after proposal space (before_after, a key of content/spaces.json, 2026-09-28):
    pinned while the after is brushed over the before as the reader scrolls. A page may still carry a plain
    hero_image instead. English opens by default (site owner, 2026-09-26); the Hebrew twin sits behind the switch.
    A guide (section "guide") renders to Fable's guide design (2026-09-29, the block above)."""
    url = f"{SITE}/{p['path'].strip('/')}/"
    guide = p["section"] == "guide"
    ba = p.get("before_after")
    hi = p.get("hero_image")
    hero_src = (hi or {}).get("src")
    if guide and hero_src and hero_src.endswith(".svg"):
        hero_src = None  # no link preview can show an SVG: a guide's og.jpg goes in og_image (design spec 5.7)
    og = SITE + (p.get("og_image") or (sc.space_og(ba) if ba else None) or hero_src or "/og-image.jpg")
    kicker, kicker_he = kickers(p)
    hero = ""
    if ba:
        hero = "\n  " + sc.before_after(ba, first=True)
    elif hi and guide:
        d = sc.image_dims(hi)
        dims = f' width="{d[0]}" height="{d[1]}"' if d else ''
        hero = f'''
  <figure class="pfig dia">
    <img src="{hi['src']}" {sc.img_alt(hi.get('alt_en', ''), hi.get('alt_he', ''))}{dims} loading="eager" fetchpriority="high" decoding="async">
    <figcaption><span class="fig-n">{T('Figure 1', 'תרשים 1')}</span>{T(H.escape(hi.get("caption_en", "")), H.escape(hi.get("caption_he", "")))}</figcaption>
  </figure>'''
    elif hi:
        cap = ""
        if hi.get("caption_en") or hi.get("caption_he"):
            cap = f'\n    <figcaption>{T(H.escape(hi.get("caption_en", "")), H.escape(hi.get("caption_he", "")))}</figcaption>'
        dims = f' width="{hi["w"]}" height="{hi["h"]}"' if hi.get("w") and hi.get("h") else ''
        tall = ' tall' if hi.get("w") and hi.get("h") and hi["h"] > hi["w"] else ''
        hero = f'''
  <figure class="pfig{tall} reveal">
    <img src="{hi['src']}" {sc.img_alt(hi.get('alt_en', ''), hi.get('alt_he', ''))}{dims} loading="eager" fetchpriority="high" decoding="async">{cap}
  </figure>'''
    if p["section"] == "area":
        top = crumbs_html(p)
    elif guide:
        top = guide_crumbs(p)
    else:
        top = f'<p class="eyebrow">{T(H.escape(kicker), H.escape(kicker_he))}</p>'
    body_en, body_he = lazy_images(p['body_en']), lazy_images(p['body_he'])
    prose = "prose"
    if guide:
        start = 2 if (hi and not ba) else 1  # the hero diagram is Figure 1
        body_en, body_he = h2_ids(number_figures(body_en, "en", start), number_figures(body_he, "he", start))
        prose = "prose guide"
    head = f'''
<header class="phead{' guide' if guide else ''}">
  {top}
  <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
  <p class="lead">{T(p['lead_en'], p['lead_he'])}</p>{guide_byline(p) if guide else ''}{hero}
</header>

<section class="section wrap tight">
  <div class="{prose}" data-l="he" dir="rtl">
{body_he}
  </div>
  <div class="{prose}" data-l="en">
{body_en}
  </div>
</section>
'''
    if guide:  # the CTA before Read next: the reader who finished a how-to is warm (design spec 2.9)
        body = head + f'''{faq_html(p, "guide-faq")}
<section class="section wrap tight">{cta_html(p)}
</section>
{guide_next(p, all_pages)}{radar_html(p)}'''
    else:
        body = head + f'''{page_guides(p, all_pages)}{faq_html(p)}{radar_html(p)}
<section class="section wrap tight">{cta_html(p)}
  {related_html(p, all_pages)}
</section>
'''
    return (sc.head(f"{p.get('head_title') or p['title_en']} · THEODORA", p["meta_description"], url, og_image=og,
                    og_type="website" if p["section"] == "area" else "article", og_title=p.get("og_title"),
                    lang="en", ld=ld_blocks(p, url, og), extra=sc.ba_preload(ba) if ba else '')
            + sc.body_open() + page_nav(p) + body + sc.tail(scripts='\n'.join(filter(None, [sc.BA_SCRIPT if ba else '', sc.WM_SUB_H1_JS if p.get('nav_sub_en') else '']))))


def page_nav(p):
    """The nav, with the small line under the wordmark when the page JSON has nav_sub_en and nav_sub_he
    (/for-designers/, Ron, 2026-09-29; shown by WM_SUB_H1_JS once the h1 has scrolled away)."""
    return sc.nav(sub=(p['nav_sub_en'], p['nav_sub_he'])) if p.get('nav_sub_en') else sc.nav()


def render_project_page(p, all_pages, projects):
    """A project: full-bleed hero, one serif lead, the story, three more projects, the next one."""
    url = f"{SITE}/{p['path'].strip('/')}/"
    hero = p.get("hero_image")
    og = SITE + (p.get("og_image") or (hero or {}).get("src") or "/og-image.jpg")
    kicker, kicker_he = kickers(p)
    i = projects.index(p)
    nxt = projects[(i + 1) % len(projects)]
    more = [projects[(i + j) % len(projects)] for j in (1, 2, 3)]
    if hero:
        header = f'''
<header class="phero">
  <img src="{hero['src']}" {sc.img_alt(hero.get('alt_en', ''), hero.get('alt_he', ''))} fetchpriority="high">
  <div class="scrim"></div>
  <div class="title">
    <p class="eyebrow">{T('Projects · ' + H.escape(kicker), 'פרויקטים · ' + H.escape(kicker_he))}</p>
    <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
    <p class="cap">{T(H.escape(hero.get('caption_en', '')), H.escape(hero.get('caption_he', '')))}</p>
  </div>
</header>
'''
    else:  # no clean photograph of this project yet: a typographic hero, never another project's photo (2026-09-28)
        header = f'''
<header class="phero type">
  <div class="title">
    <p class="eyebrow">{T('Projects · ' + H.escape(kicker), 'פרויקטים · ' + H.escape(kicker_he))}</p>
    <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
  </div>
</header>
'''
    body = header + f'''
<section class="plead"><p class="reveal">{T(p['lead_en'], p['lead_he'])}</p></section>

<section class="section wrap">
  <div class="prose" data-l="he" dir="rtl">
{lazy_images(p['body_he'])}
  </div>
  <div class="prose" data-l="en">
{lazy_images(p['body_en'])}
  </div>
</section>
{faq_html(p)}
<section class="section wrap">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('More projects', 'עוד פרויקטים')}</p></div><a class="arrow" href="/projects/"><span class="ln"></span>{T('Projects', 'פרויקטים')}</a></div>
  <div class="grid3">{''.join(sc.project_card(q) for q in more)}
  </div>
  <div class="next reveal">
    <p class="eyebrow">{T('Next project', 'הפרויקט הבא')}</p>
    <a class="big" href="/{nxt['path'].strip('/')}/">{T(H.escape(nxt['title_en']), H.escape(nxt['title_he']))}</a>
    {related_html(p, all_pages, exclude_projects=True)}
  </div>
</section>
'''
    return (sc.head(f"{p.get('head_title') or p['title_en']} · THEODORA", p["meta_description"], url, og_image=og, og_type="article",
                    lang="en", ld=ld_blocks(p, url, og))
            + sc.body_open() + sc.nav() + body + sc.tail())


def ba_card(p):
    """A hub card for a page whose hero is a before/after proposal: the after, marked a proposal."""
    k = p["before_after"]
    return f'''
      <a class="card reveal" href="/{p['path'].strip('/')}/">
        <div class="ph"><img src="/images/spaces/{k}_after-1000.webp" {sc.img_alt(sc.spaces()[k]['alt_en'], sc.spaces()[k].get('alt_he', ''))} loading="lazy"><span class="ba-chip">{T('Proposal', 'הצעה')}</span></div>
        <h3 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h3>
        <p class="muted">{T(H.escape(sc.first_sentence(p['lead_en'])), H.escape(sc.first_sentence(p['lead_he'])))}</p>
      </a>'''


def render_hub(section, title_en, title_he, lead_en, lead_he, pages, hero_src, hero_alt, guides=()):
    """A hub: the hero, the cards, and on /advisory/ the guides group after them (guides: the guide pages with a hero
    diagram, as .gcards; Fable's design, 2026-09-29). Every card and every guide is in the CollectionPage's hasPart."""
    url = f"{SITE}/{section}/"
    cards = "".join(sc.project_card(p) if (p.get("hero_image") or p["section"] == "projects") else ba_card(p) if p.get("before_after") else f'''
      <a class="card reveal" href="/{p['path'].strip('/')}/">
        <h3 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h3>
        <p class="muted">{T(H.escape(strip_tags(p['meta_description'])), H.escape(snippet(p.get('lead_he') or '')))}</p>
      </a>''' for p in pages)
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title_en, "url": url, "inLanguage": ["en", "he"],
           "isPartOf": {"@id": SITE + "/#site"},
           "hasPart": [{"@type": "WebPage", "name": p["title_en"], "url": f"{SITE}/{p['path'].strip('/')}/"} for p in list(pages) + list(guides)]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"},
               {"@type": "ListItem", "position": 2, "name": title_en, "item": url}]}]
    body = f'''
<header class="phero" style="height: 62vh; min-height: 480px;">
  <img src="{hero_src}" alt="{H.escape(hero_alt, quote=True)}" fetchpriority="high">
  <div class="scrim"></div>
  <div class="title">
    <p class="eyebrow">{T(H.escape(title_en), H.escape(title_he))}</p>
    <h1 class="serif">{T(lead_en, lead_he)}</h1>
  </div>
</header>

<section class="section wrap tight">
  <div class="grid3">{cards}
  </div>
</section>{sc.guides_section(list(guides), GUIDES_HUB_H2, GUIDES_HUB_SUB, tight=True)}
{who_row(section)}
<section class="section wrap tight">
  <div class="cta reveal">
    <h2 class="serif">{T(CTA_EN, CTA_HE)}</h2>
    <a class="btn" href="{MAIL}">{T('Write to Stav', 'כתבו לסתיו')}</a>
    {sc.phone_link('cta')}
  </div>
</section>
'''
    desc = strip_tags(lead_en)[:158]
    return (sc.head(f"{title_en} · THEODORA", desc, url, og_image=SITE + hero_src, lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail())


def who_row(section):
    """The projects hub's Who I work with row (Ron's SEO brief, 2026-09-29, P1.5): the seven pages for one kind of
    client each, the same list as every footer (site_chrome.WHO_I_WORK_WITH)."""
    if section != "projects":
        return ""
    links = "".join(f'<a href="{u}">{T(en, he)}</a>' for u, en, he in sc.WHO_I_WORK_WITH)
    return f'''
<section class="section wrap tight">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('Who I work with', 'עם מי אני עובדת')}</p></div></div>
  <div class="readnext who-row reveal">{links}</div>
</section>
'''


# /contact/ (Ron's SEO brief, 2026-09-29, P1.1): a real, indexable page in place of the old redirect stub to /#contact.
# The phone, the email with the mail fallback panel, the contact form once site_chrome.FORM_ENDPOINT is set, the service
# area, Art Radar on WhatsApp and the Yelp listing. No hours until Ron confirms them. No street address, ever.
CONTACT = {
    "path": "contact",
    "title": "Contact THEODORA, Art Advisor in Tenafly, NJ",
    "description": "Call (201) 351-8367 or email stav@stavtheodor.com. Send one photo of the wall and a line about the space. Serving Tenafly, Bergen County, NJ and NYC.",
    "h1": ("Contact Stav", "יצירת קשר עם סתיו"),
    "area": ("Based in Tenafly, New Jersey. Serving Tenafly, Bergen County, New Jersey and New York City, with projects in Tel Aviv.",
             "מבוססת בטנפליי, ניו ג'רזי. משרתת את טנפליי, מחוז ברגן, ניו ג'רזי וניו יורק, עם פרויקטים בתל אביב."),
    "yelp": ("Find THEODORA on Yelp", "THEODORA ב-Yelp"),
}


# The service area as a row of place names on /contact/ (2026-09-29), beside the full sentence in CONTACT["area"]
CONTACT_PLACES = [("Tenafly", "טנפליי"), ("Bergen County", "מחוז ברגן"), ("New Jersey", "ניו ג'רזי"),
                  ("New York City", "ניו יורק"), ("Tel Aviv", "תל אביב")]


def render_contact():
    """/contact/ (redesigned 2026-09-29): the h1 and the closing line, then the same contact block as the homepage's
    #contact (site_chrome.contact_act: the three ways, What happens next, the form), then the service area. The footer
    under it is the quiet one (no second closing block)."""
    url = f"{SITE}/{CONTACT['path']}/"
    intro_en, intro_he = sc.FOOTER_CTA
    ld = [{"@type": "ContactPage", "@id": url + "#page", "url": url, "name": CONTACT["title"],
           "about": {"@id": SITE + "/#org"}, "inLanguage": ["en", "he"]},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Contact", "item": url}]}]
    places = "".join(f"<li>{T(en, he)}</li>" for en, he in CONTACT_PLACES)
    body = f'''
<header class="phead contact-head">
  <p class="eyebrow">{T('Contact', 'יצירת קשר')}</p>
  <h1 class="serif">{T(*CONTACT["h1"])}</h1>
  <p class="lead">{T(intro_en, intro_he)}</p>
</header>

<section class="section wrap tight contact-page">
  {sc.contact_act(f"/{CONTACT['path']}/", h='h2', loc='contact')}
  <div class="contact-area reveal">
    <p class="eyebrow">{T('Where I work', 'איפה אני עובדת')}</p>
    <ul class="places">{places}</ul>
    <p class="area">{T(*CONTACT["area"])}</p>
    <div class="more">
      <a class="arrow" href="{sc.WHATSAPP}" target="_blank" rel="noopener"><span class="ln"></span>{T('Art Radar on WhatsApp', 'ראדאר אמנות בוואטסאפ')}</a>
      <a class="arrow" href="{sc.YELP}" target="_blank" rel="noopener"><span class="ln"></span>{T(*CONTACT["yelp"])}</a>
    </div>
  </div>
</section>
'''
    return (sc.head(CONTACT["title"], CONTACT["description"], url, lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail(scripts=sc.form_js(), quiet=True))


# /about/ (2026-09-29): a real, indexable About page in place of the old redirect stub to /#about. The opening paragraph
# states the entity facts in plain sentences (what THEODORA is, who runs it, where, for whom, how to reach her); everything
# after it is copy already published on the site, read from its source at build time so the two never drift: the
# homepage's #about and #what-i-do paragraphs and service lines (templates/home.html), the partner pages' two promises
# (content/pages/for-designers.json, for-brokers.json) and the page titles of the pages it links. No new claim.
ABOUT = {
    "path": "about",
    "title": "About THEODORA | Art Advisor Stav Theodor, Tenafly NJ",
    "description": "THEODORA is the art curation and advisory practice of Stav Theodor in Tenafly, NJ, serving Bergen County, New Jersey and New York City.",
    "h1": ("About THEODORA and Stav Theodor", "אודות THEODORA וסתיו תאודור"),
    # The opening portrait (the Tenafly page's hero, a real photograph); stav-portrait.jpg stays the og:image
    "portrait": ("/images/projects/stav-couch.webp", 1000, 1250,
                 "Stav Theodor seated on a pale linen sofa beneath a framed painting of a woman playing the piano, hung on a walnut panelled wall",
                 "סתיו תאודור יושבת על ספה מפשתן בהיר, מתחת לציור ממוסגר של אישה מנגנת בפסנתר, התלוי על קיר מחופה עץ אגוז"),
    "og_image": "/images/stav-portrait.jpg",
    # The credentials sentence the homepage's #about carried until 2026-09-29 (its facts are now the credentials strip there)
    "credentials": ("I am an art curator with an M.A. in art history from the Faculty of Arts at Ben-Gurion University and a diploma in curatorial and museum studies from the Faculty of Arts at Tel Aviv University. Today I am based in Tenafly, New Jersey, and work in New York, across Bergen County and in Tel Aviv.",
                    "אני אוצרת אמנות, בעלת תואר שני בתולדות האמנות מהפקולטה למדעי הרוח והחברה באוניברסיטת בן-גוריון ותעודה בלימודי אוצרות ומוזיאולוגיה מהפקולטה לאמנויות באוניברסיטת תל אביב. היום הבסיס שלי בטנפליי, ניו ג'רזי, ואני עובדת בניו יורק, ברחבי מחוז ברגן ובתל אביב."),
    # Two real project photographs, each with a caption already published on its project page (read at build time):
    # (page path, image src, width, height, where the caption comes from: "hero" or the body figure)
    "photos": [("projects/creating-hope-exhibition-un-geneva", "/images/projects/stav-gallery.jpg", 1600, 1153, "hero"),
               ("projects/caesarea-sea-view-villa-triptych", "/images/projects/storks-wall.jpg", 1600, 1200, "body")],
}
# The disambiguation line (Ron, 2026-09-29): AI engines mixed THEODORA up with two unrelated advisories with similar
# names. The same sentence closes the /about/ opening paragraph, sits in content/entity.json (disambiguatingDescription),
# llms.txt, answers.md and agent.txt.
DISAMBIG = ("THEODORA Art Advisory by Stav Theodor is based in Tenafly, New Jersey, and is not affiliated with "
            "Theadora Art Advisory (Los Angeles) or TSG Art Advisory.",
            "THEODORA Art Advisory by Stav Theodor פועלת מטנפליי, ניו ג'רזי, ואינה קשורה ל-Theadora Art Advisory "
            "(לוס אנג'לס) או ל-TSG Art Advisory.")
# The places, in the footer's words and order (site_chrome.footer)
ABOUT_PLACES = [
    ("/art-consultant-tenafly-nj/", "Art consultant in Tenafly", "יועצת אמנות בטנפליי"),
    ("/art-advisor-bergen-county/", "Art advisor in Bergen County", "יועצת אמנות במחוז ברגן"),
    ("/art-curator-new-jersey/", "Art consultant in New Jersey", "יועצת אמנות בניו ג'רזי"),
    ("/art-curator-new-york/", "Art advisor in New York", "יועצת אמנות בניו יורק"),
]
# Who I work with on /about/: the footer's seven client pages plus the two audiences without a page of their own
# (AGENTS.md: designers, private collectors, home and business owners), in the order of the entity's opening sentence.
ABOUT_WHO_EXTRA = [(None, "Private collectors", "אספנים פרטיים"), (None, "Home and business owners", "בעלי בתים ובעלי עסקים")]


def home_twins(region):
    """Twins read from templates/home.html: a variant region's (en, he) by its name; 'about' for the (en, he) of each
    body paragraph of the #about section; 'about_line' for its serif statement; 'creds' for the credentials strip's
    markup, whole; 'services' for the ((en, he) heading, (en, he) line) of each service column."""
    tpl = open("templates/home.html", encoding="utf-8").read()
    pair = re.compile(r'<span data-l="en">(.*?)</span><span data-l="he" dir="rtl">(.*?)</span>', re.S)
    about = re.search(r'<section class="section wrap" id="about">(.*?)</section>', tpl, re.S).group(1)
    if region == "about":
        return [pair.match(m).groups() for m in re.findall(r'<p class="body">(.*?)</p>', about, re.S)]
    if region == "about_line":
        return pair.search(re.search(r'<h2 class="serif about-line">(.*?)</h2>', about, re.S).group(1)).groups()
    if region == "creds":
        return re.search(r'<dl class="creds[^"]*">.*?</dl>', about, re.S).group(0)
    if region == "services":
        sec = re.search(r'<section class="cols" id="services"[^>]*>(.*?)</section>', tpl, re.S).group(1)
        return [(pair.search(h).groups(), pair.search(d).groups())
                for h, d in re.findall(r'<h3 class="serif">(.*?)</h3><p class="desc">(.*?)</p>', sec, re.S)]
    return pair.search(re.search(rf'<!--variant:{region}-->(.*?)<!--/variant:{region}-->', tpl, re.S).group(1)).groups()


def page_by_path(pages, path):
    return next(p for p in pages if p["path"].strip("/") == path)


def about_rows(pages):
    """The reading rows of /about/: [(h2 (en, he), [(en, he) block, ...])]; every sentence is the site's own, published
    elsewhere. A block is a paragraph's inner html, or ('ul', [(en, he) item, ...])."""
    bg = home_twins("about")  # [experience and THEODORA, before THEODORA and recent projects]
    statement = home_twins("intro_statement")
    how = home_twins("what_i_do_p1")
    where = home_twins("what_i_do_p2")
    services = home_twins("services")
    des, bro, adv = (page_by_path(pages, x) for x in ("for-designers", "for-brokers", "for-advisors"))
    credit = ("The credit is yours. I say so to the buyer.", "הקרדיט שלכם. אני אומרת את זה לקונה.")
    for text, src in ((credit[0], bro["body_en"]), (credit[1], bro["body_he"])):
        assert text in src, "the brokers' promise changed on /for-brokers/; update the copy of it in about_rows()"
    tenafly = page_by_path(pages, "art-consultant-tenafly-nj")
    bg_h2 = (re.findall(r"<h2>(.*?)</h2>", tenafly["body_en"])[5], re.findall(r"<h2>(.*?)</h2>", tenafly["body_he"])[5])
    assert bg_h2 == ("My background", "הרקע שלי"), bg_h2
    link = lambda p, lang: f'<a href="/{p["path"].strip("/")}/">{H.escape(p["title_" + lang])}</a>'
    both = lambda f: tuple(f(i, lang) for i, lang in enumerate(("en", "he")))
    return [
        (bg_h2, [bg[0], bg[1], ABOUT["credentials"]]),
        (("What I do", "מה אני עושה"), [statement, how,
                                       ("ul", [both(lambda i, _: f"<strong>{h[i]}.</strong> {d[i]}.") for h, d in services])]),
        (("Where I work", "איפה אני עובדת"), [where]),
        (("For partners", "לשותפים"), [both(lambda i, l: f'{des["lead_" + l]} {link(des, l)}.'),
                                       both(lambda i, l: f"{credit[i]} {link(bro, l)}."),
                                       both(lambda i, l: f"{link(adv, l)}.")]),
    ]


def about_rows_html(pages):
    out = ""
    for (h_en, h_he), blocks in about_rows(pages):
        cols = []
        for i, lang in enumerate(("en", "he")):
            html = ""
            for b in blocks:
                if b[0] == "ul":
                    html += "<ul>" + "".join(f"<li>{it[i]}</li>" for it in b[1]) + "</ul>"
                else:
                    html += f"<p>{b[i]}</p>"
            cols.append(html)
        out += f'''
  <div class="story-row reveal">
    <h2 class="serif">{T(h_en, h_he)}</h2>
    <div class="prose" data-l="en">{cols[0]}</div>
    <div class="prose" data-l="he" dir="rtl">{cols[1]}</div>
  </div>'''
    return out


def about_photos(pages):
    """Two real project photographs, each captioned with the words its project page already gives it."""
    figs = ""
    for path, src, w, h, where in ABOUT["photos"]:
        p = page_by_path(pages, path)
        if where == "hero":
            hi = p["hero_image"]
            assert hi["src"] == src, (path, hi["src"])
            alt, cap = (hi["alt_en"], hi["alt_he"]), (hi["caption_en"], hi["caption_he"])
        else:
            got = []
            for lang in ("en", "he"):
                m = re.search(rf'<img src="{re.escape(src)}" alt="([^"]*)"\s*/?><figcaption>(.*?)</figcaption>', p["body_" + lang])
                assert m, f"{path}: the figure with {src} left the {lang} body; update ABOUT['photos']"
                got.append(m.groups())
            alt, cap = (got[0][0], got[1][0]), (got[0][1], got[1][1])
        figs += f'''
    <figure class="about-photo reveal">
      <a href="/{path}/"><img src="{src}" {sc.img_alt(*alt)} width="{w}" height="{h}" loading="lazy" decoding="async"></a>
      <figcaption><a href="/{path}/">{T(H.escape(p["title_en"]), H.escape(p["title_he"]))}</a>{T(cap[0], cap[1], cls="cap")}</figcaption>
    </figure>'''
    return figs


def about_links(pages):
    """Where else to go from /about/: the advisory pages, the places, projects and contact, as three columns."""
    adv = [p for p in pages if p["section"] in ("advisory", "guide")]
    cols = [
        (("Art advisory", "ייעוץ אמנות"), [("/advisory/", "Art advisory", "ייעוץ אמנות")]
         + [(f'/{p["path"].strip("/")}/', p["title_en"], p["title_he"]) for p in adv]),
        (("Where I work", "איפה אני עובדת"), ABOUT_PLACES),
        (("Projects", "פרויקטים"), [("/projects/", "Projects", "פרויקטים"), ("/contact/", "Contact", "יצירת קשר")]),
    ]
    html = ""
    for (h_en, h_he), links in cols:
        a = "".join(f'<a href="{u}">{T(H.escape(en), H.escape(he))}</a>' for u, en, he in links)
        html += f'''
    <div><p class="eyebrow">{T(h_en, h_he)}</p><div class="readnext">{a}</div></div>'''
    return html


def render_about(pages):
    """/about/ (redesigned 2026-09-29): a portrait-led opening (the homepage's serif statement, the h1 as a quiet line,
    the entity paragraph), the homepage's credentials strip, the practice story in short rows, Who I work with, two
    real project photographs, the links, and a closing call to /contact/."""
    url = f"{SITE}/{ABOUT['path']}/"
    src, w, h, alt_en, alt_he = ABOUT["portrait"]
    line = home_twins("about_line")
    tel = f'<a href="{sc.PHONE_TEL}" data-loc="about" dir="ltr">{sc.PHONE}</a>'
    mail = f'<a href="{MAIL}" data-loc="about" dir="ltr">{sc.EMAIL}</a>'
    lead_en = ("THEODORA Art Advisory by Stav Theodor is an art curation and advisory practice, founded and run by Stav Theodor, an art curator and advisor. "
               "THEODORA is based in Tenafly, New Jersey, and serves Tenafly, Bergen County, New Jersey and New York City, with projects in Tel Aviv. "
               "It works with private homes, interior designers and architects, private collectors, law firms, investment firms, "
               f"wealth managers, medical practices, restaurants and boutique hotels. To reach Stav, call {tel} or email {mail}. "
               + DISAMBIG[0])
    lead_he = ("THEODORA Art Advisory by Stav Theodor היא פרקטיקה של אוצרות וייעוץ אמנות, שייסדה ומנהלת סתיו תאודור, אוצרת ויועצת אמנות. "
               "THEODORA מבוססת בטנפליי, ניו ג'רזי, ומשרתת את טנפליי, מחוז ברגן, ניו ג'רזי וניו יורק, עם פרויקטים בתל אביב. "
               "היא עובדת עם בתים פרטיים, מעצבי פנים ואדריכלים, אספנים פרטיים, משרדי עורכי דין, חברות השקעה, "
               f"מנהלי הון, מרפאות, מסעדות ומלונות בוטיק. ליצירת קשר עם סתיו: התקשרו ל-{tel} או כתבו ל-{mail}. "
               + DISAMBIG[1])
    who = [sc.WHO_I_WORK_WITH[0]] + ABOUT_WHO_EXTRA + sc.WHO_I_WORK_WITH[1:]
    who_html = "".join(
        (f'<a class="who-item" href="{u}"><span class="nm">{T(en, he)}</span><span class="ln"></span></a>' if u
         else f'<span class="who-item"><span class="nm">{T(en, he)}</span></span>') for u, en, he in who)
    ld = [{"@type": "AboutPage", "@id": url + "#page", "url": url, "name": ABOUT["title"], "description": ABOUT["description"],
           "inLanguage": ["en", "he"], "isPartOf": {"@id": SITE + "/#site"},
           "mainEntity": [{"@id": SITE + "/#org"}, {"@id": SITE + "/#stav"}], "about": {"@id": SITE + "/#org"},
           "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + src}},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "About", "item": url}]}]
    body = f'''
<header class="about-hero wrap">
  <figure class="ah-portrait"><img src="{src}" {sc.img_alt(alt_en, alt_he)} width="{w}" height="{h}" loading="eager" fetchpriority="high" decoding="async"></figure>
  <div class="ah-text">
    <p class="eyebrow">{T('About', 'אודות')}</p>
    <p class="serif ah-line">{T(*line)}</p>
    <h1 class="ah-h1">{T(*ABOUT["h1"])}</h1>
    <p class="ah-lead">{T(lead_en, lead_he)}</p>
    <p class="about-sig"><span class="nm">{T('Stav Theodor&#8209;Kimhi', 'סתיו תאודור&#8209;קמחי')}</span><span class="role">{T('Founder, art curator and advisor', 'מייסדת, אוצרת ויועצת אמנות')}</span></p>
  </div>
</header>

<section class="section wrap tight">
  {home_twins("creds")}
</section>

<section class="section wrap story">{about_rows_html(pages)}
</section>

<section class="section wrap">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('Who I work with', 'עם מי אני עובדת')}</p><h2 class="serif">{T('Art for every kind of space', 'אמנות לכל סוג של חלל')}</h2></div></div>
  <div class="who-grid reveal">{who_html}</div>
</section>

<section class="section wrap">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('Projects', 'פרויקטים')}</p></div><a class="arrow" href="/projects/"><span class="ln"></span>{T('All projects', 'כל הפרויקטים')}</a></div>
  <div class="about-photos">{about_photos(pages)}
  </div>
</section>

<section class="section wrap tight">
  <div class="about-more reveal">{about_links(pages)}
  </div>
</section>

<section class="section wrap">
  <div class="about-cta reveal">
    <h2 class="serif">{T(CTA_EN, CTA_HE)}</h2>
    <div class="acts">
      <a class="btn solid" href="/contact/">{T('Contact Stav', 'יצירת קשר עם סתיו')}</a>
      <a class="arrow" href="{MAIL}"><span class="ln"></span>{T('Write to Stav', 'כתבו לסתיו')}</a>
      {sc.phone_link('cta')}
    </div>
  </div>
</section>
'''
    return (sc.head(ABOUT["title"], ABOUT["description"], url, og_image=SITE + ABOUT["og_image"], lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail(quiet=True))


def check(p, out):
    bad = []
    if sc.dash_leftovers(sc.undash_html(out)): bad.append("em/en dash the sanitizer cannot place")
    if re.search(r"\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1 ?\(?\d{3}", out.replace(sc.PHONE_TEL, "").replace(sc.PHONE_SCHEMA, "").replace(sc.PHONE, "")):
        bad.append("phone number other than the business line")
    for k in ["title_en", "title_he", "lead_en", "lead_he", "body_en", "body_he", "meta_description"]:
        if not p.get(k): bad.append(f"missing {k}")
    if p["section"] == "projects" and not p.get("hero_image") and not (p.get("place_en") and p.get("place_he")):
        bad.append("project page without hero_image needs place_en and place_he for its card")
    if p.get("before_after") and p["before_after"] not in sc.spaces(): bad.append(f"before_after {p['before_after']} not in content/spaces.json")
    if p["section"] == "area":
        for k in ("breadcrumb", "service", "og_title"):
            if not p.get(k): bad.append(f"town or county page without {k}")
    return bad


PROJECT_ORDER = [
    'caesarea-garden-villa', 'caesarea-sea-view-villa-triptych', 'closter-new-jersey-new-construction',
    'herzliya-pituach-sea-view-apartment', 'hod-hasharon-private-villa', 'ramat-gan-private-home',
    'caesarea-private-estate', 'caesarea-luxury-residence-home-office', 'manhattan-skyline-residence',
    'tel-aviv-bauhaus-residence', 'tel-aviv-home-of-roni-daloomi', 'tel-aviv-private-residence-shtisel-commission',
    'tel-aviv-renovated-bauhaus-home', 'hotels-and-hospitality-collections', 'creating-hope-exhibition-un-geneva',
]


def ordered_projects(pages):
    by = {p["slug"]: p for p in pages if p["section"] == "projects"}
    missing = [s for s in PROJECT_ORDER if s not in by]
    assert not missing, missing
    extra = sorted(s for s in by if s not in PROJECT_ORDER)
    return [by[s] for s in PROJECT_ORDER + extra]


def ordered_guides(pages):
    """The hub's guides group: every built guide with a hero diagram, in GUIDE_ORDER, then the rest newest first."""
    gs = [p for p in sc.hub_guides(pages) if not check(p, "")]
    known = [next(p for p in gs if p["slug"] == s) for s in GUIDE_ORDER if any(p["slug"] == s for p in gs)]
    return known + sorted((p for p in gs if p not in known), key=lambda p: p.get("date", ""), reverse=True)


HUBS = {
    "advisory": ("Art advisory, answered plainly", "ייעוץ אמנות, בשפה פשוטה",
                 "What an art advisor does, what it costs, and how the work goes from a first conversation to a piece on the wall. Written for people who are about to buy, build, or move.",
                 "מה יועצת אמנות עושה, כמה זה עולה, ואיך התהליך מתקדם משיחה ראשונה ועד יצירה על הקיר. נכתב לאנשים שעומדים לקנות, לבנות או לעבור דירה.",
                 "/images/home2/col-curation.jpg", "Stav Theodor holding a framed work in a gallery corridor lined with paintings"),
    "projects": ("Projects", "פרויקטים",
                 "Homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels from Chengdu to Amman, and one exhibition that reached Geneva. Each page tells what the space asked for and what answered it.",
                 "בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות מצ'נגדו ועד עמאן, ותערוכה אחת שהגיעה לז'נבה. כל עמוד מספר מה החלל ביקש ומה ענה לו.",
                 "/images/home2/garden-villa.jpg", "Foyer of a Caesarea garden villa, two tall portraits facing the front door"),
}


def main():
    sc.guard_index()
    # every page JSON passes tools/check_pages.py before anything is written (2026-09-27): every file under content/ is
    # served publicly, so a page carrying an internal key (editor_note, or a key starting with "_" or "note") stops the build
    if subprocess.run([sys.executable, "tools/check_pages.py"] + sorted(glob.glob("content/pages/*.json"))).returncode:
        sys.exit("build-site-pages: tools/check_pages.py failed, nothing was written (content/PAGE-SPEC.md)")
    pages = load_pages()
    projects = ordered_projects(pages)
    problems = 0
    for p in pages:
        out = render_project_page(p, pages, projects) if p["section"] == "projects" else render_article_page(p, pages)
        bad = check(p, out)
        if bad:
            print(f"  BLOCKED {p['path']}: {', '.join(bad)}"); problems += 1; continue
        d = p["path"].strip("/")
        sc.write(os.path.join(d, "index.html"), out)
        print(f"  wrote {d}/index.html")
    sc.write(os.path.join(CONTACT["path"], "index.html"), render_contact())
    print(f"  wrote {CONTACT['path']}/index.html" + (" (with the contact form)" if sc.FORM_ENDPOINT else " (no form: site_chrome.FORM_ENDPOINT is empty)"))
    sc.write(os.path.join(ABOUT["path"], "index.html"), render_about(pages))
    print(f"  wrote {ABOUT['path']}/index.html")
    for sec, (te, th, le, lh, hero_src, hero_alt) in HUBS.items():
        if sec == "projects":
            sec_pages = projects
        else:  # the advisory hub: the two local landing pages first, the town and county pages, then the advisory pages,
            # then the guides whose hero is a before/after (the ten questions guide) as advisory cards; the guides with a
            # hero diagram get their own group after the cards (Fable's design, 2026-09-29; ordered_guides)
            sec_pages = ([p for p in pages if p["section"] == "local"] + [p for p in pages if p["section"] == "area"] + [p for p in pages if p["section"] == sec]
                         + [p for p in pages if p["section"] == "guide" and not p.get("hero_image")])
        sec_pages = [p for p in sec_pages if not check(p, "")]
        guides = ordered_guides(pages) if sec == "advisory" else []
        if not sec_pages: continue
        sc.write(os.path.join(sec, "index.html"), render_hub(sec, te, th, le, lh, sec_pages, hero_src, hero_alt, guides))
        print(f"  wrote {sec}/index.html ({len(sec_pages)} cards" + (f", {len(guides)} guides" if guides else "") + ")")
    if "--no-sitemap" not in sys.argv:
        subprocess.run([sys.executable, "build-post-pages.py"], check=True)
    if problems: sys.exit(1)


if __name__ == "__main__":
    main()
