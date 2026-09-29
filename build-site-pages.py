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
CRUMB_NAME = {"advisory": "Advisory", "local": "Advisory", "projects": "Projects", "partners": "Working together", "guide": "Guides"}
CRUMB_DIR = {"advisory": "advisory", "local": "advisory", "projects": "projects"}
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
    main.update(p.get("schema_extra", {}))
    crumbs = [{"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"}]
    if p["section"] in CRUMB_DIR:  # sections with a hub page get a middle crumb; partners and the guide go straight to the page
        crumbs.append({"@type": "ListItem", "position": 2, "name": CRUMB_NAME[p["section"]], "item": SITE + "/" + CRUMB_DIR[p["section"]] + "/"})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": p["title_en"], "item": url})
    ld = [main, {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs}]
    if p.get("faq"):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "en",
                   "mainEntity": [{"@type": "Question", "name": q["q_en"], "acceptedAnswer": {"@type": "Answer", "text": strip_tags(q["a_en"])}} for q in p["faq"]]})
    return ld


def faq_html(p):
    if not p.get("faq"):
        return ""
    qas = "".join(f'''
      <details class="qa">
        <summary><h3 class="serif">{T(H.escape(q["q_en"]), H.escape(q["q_he"]))}</h3><span class="plus" aria-hidden="true"></span></summary>
        <p class="body">{T(q["a_en"], q["a_he"])}</p>
      </details>''' for q in p["faq"])
    return f'''
<section class="section wrap">
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


def render_article_page(p, all_pages):
    """Advisory, partner and guide pages: text header, the hero figure, the reading column.
    The hero figure is a before/after proposal space (before_after, a key of content/spaces.json, 2026-09-28):
    pinned while the after is brushed over the before as the reader scrolls. A page may still carry a plain
    hero_image instead. English opens by default (site owner, 2026-09-26); the Hebrew twin sits behind the switch."""
    url = f"{SITE}/{p['path'].strip('/')}/"
    ba = p.get("before_after")
    og = SITE + (p.get("og_image") or (sc.space_og(ba) if ba else None) or (p.get("hero_image") or {}).get("src") or "/og-image.jpg")
    kicker, kicker_he = kickers(p)
    hero = ""
    hi = p.get("hero_image")
    if ba:
        hero = "\n  " + sc.before_after(ba, first=True)
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
    top = crumbs_html(p) if p["section"] == "area" else f'<p class="eyebrow">{T(H.escape(kicker), H.escape(kicker_he))}</p>'
    body = f'''
<header class="phead">
  {top}
  <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
  <p class="lead">{T(p['lead_en'], p['lead_he'])}</p>{hero}
</header>

<section class="section wrap tight">
  <div class="prose" data-l="he" dir="rtl">
{lazy_images(p['body_he'])}
  </div>
  <div class="prose" data-l="en">
{lazy_images(p['body_en'])}
  </div>
</section>
{faq_html(p)}{radar_html(p)}
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


def render_hub(section, title_en, title_he, lead_en, lead_he, pages, hero_src, hero_alt):
    url = f"{SITE}/{section}/"
    cards = "".join(sc.project_card(p) if (p.get("hero_image") or p["section"] == "projects") else ba_card(p) if p.get("before_after") else f'''
      <a class="card reveal" href="/{p['path'].strip('/')}/">
        <h3 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h3>
        <p class="muted">{T(H.escape(strip_tags(p['meta_description'])), H.escape(snippet(p.get('lead_he') or '')))}</p>
      </a>''' for p in pages)
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title_en, "url": url, "inLanguage": ["en", "he"],
           "isPartOf": {"@id": SITE + "/#site"},
           "hasPart": [{"@type": "WebPage", "name": p["title_en"], "url": f"{SITE}/{p['path'].strip('/')}/"} for p in pages]},
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
</section>
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


def render_contact():
    url = f"{SITE}/{CONTACT['path']}/"
    intro_en, intro_he = sc.FOOTER_CTA
    ld = [{"@type": "ContactPage", "@id": url + "#page", "url": url, "name": CONTACT["title"],
           "about": {"@id": SITE + "/#org"}, "inLanguage": ["en", "he"]},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Contact", "item": url}]}]
    form = sc.contact_form(f"/{CONTACT['path']}/", h='h2')
    form_html = '\n    ' + form if form else ''
    body = f'''
<header class="phead">
  <p class="eyebrow">{T('Contact', 'יצירת קשר')}</p>
  <h1 class="serif">{T(*CONTACT["h1"])}</h1>
  <p class="lead">{T(intro_en, intro_he)}</p>
</header>

<section class="section wrap tight">
  <div class="contact-page">
    <a class="big-tel" href="{sc.PHONE_TEL}" data-loc="contact">{sc.PHONE}</a>
    <a class="mail" href="{MAIL}" data-loc="contact">{sc.EMAIL}</a>{form_html}
    <p class="area">{T(*CONTACT["area"])}</p>
    <div class="more">
      <a class="plain" href="{sc.WHATSAPP}" target="_blank" rel="noopener">{T('Art Radar on WhatsApp', 'ראדאר אמנות בוואטסאפ')}</a>
      <a class="plain" href="{sc.YELP}" target="_blank" rel="noopener">{T(*CONTACT["yelp"])}</a>
    </div>
  </div>
</section>
'''
    return (sc.head(CONTACT["title"], CONTACT["description"], url, lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail(scripts=sc.form_js()))


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
    "portrait": ("/images/stav-portrait.jpg", 508, 430, "Stav Theodor-Kimhi", "סתיו תאודור-קמחי"),
}
# The places, in the footer's words and order (site_chrome.footer)
ABOUT_PLACES = [
    ("/art-consultant-tenafly-nj/", "Art consultant in Tenafly", "יועצת אמנות בטנפליי"),
    ("/art-advisor-bergen-county/", "Art advisor in Bergen County", "יועצת אמנות במחוז ברגן"),
    ("/art-curator-new-jersey/", "Art consultant in New Jersey", "יועצת אמנות בניו ג'רזי"),
    ("/art-curator-new-york/", "Art advisor in New York", "יועצת אמנות בניו יורק"),
]


def home_twins(region):
    """Twins read from templates/home.html: a variant region's (en, he) by its name; 'about' for the (en, he) of each
    body paragraph of the #about section; 'services' for the ((en, he) heading, (en, he) line) of each service column."""
    tpl = open("templates/home.html", encoding="utf-8").read()
    pair = re.compile(r'<span data-l="en">(.*?)</span><span data-l="he" dir="rtl">(.*?)</span>', re.S)
    if region == "about":
        sec = re.search(r'<section class="section wrap" id="about">(.*?)</section>', tpl, re.S).group(1)
        return [pair.match(m).groups() for m in re.findall(r'<p class="body">(.*?)</p>', sec, re.S)]
    if region == "services":
        sec = re.search(r'<section class="cols" id="services"[^>]*>(.*?)</section>', tpl, re.S).group(1)
        return [(pair.search(h).groups(), pair.search(d).groups())
                for h, d in re.findall(r'<h3 class="serif">(.*?)</h3><p class="desc">(.*?)</p>', sec, re.S)]
    return pair.search(re.search(rf'<!--variant:{region}-->(.*?)<!--/variant:{region}-->', tpl, re.S).group(1)).groups()


def page_by_path(pages, path):
    return next(p for p in pages if p["path"].strip("/") == path)


def about_body(pages):
    """The reading column of /about/, (en, he): every sentence is the site's own, published elsewhere."""
    bg = home_twins("about")  # [experience, THEODORA exists, credentials], in the homepage's order ("that connection")
    statement = home_twins("intro_statement")
    how = home_twins("what_i_do_p1")
    where = home_twins("what_i_do_p2")
    services = home_twins("services")
    des, bro, adv = (page_by_path(pages, x) for x in ("for-designers", "for-brokers", "for-advisors"))
    credit = ("The credit is yours. I say so to the buyer.", "הקרדיט שלכם. אני אומרת את זה לקונה.")
    for text, src in ((credit[0], bro["body_en"]), (credit[1], bro["body_he"])):
        assert text in src, "the brokers' promise changed on /for-brokers/; update the copy of it in about_body()"
    tenafly = page_by_path(pages, "art-consultant-tenafly-nj")
    bg_h2 = (re.findall(r"<h2>(.*?)</h2>", tenafly["body_en"])[5], re.findall(r"<h2>(.*?)</h2>", tenafly["body_he"])[5])
    assert bg_h2 == ("My background", "הרקע שלי"), bg_h2
    link = lambda p, lang: f'<a href="/{p["path"].strip("/")}/">{H.escape(p["title_" + lang])}</a>'
    out = []
    for i, lang in enumerate(("en", "he")):
        li = "".join(f"<li><strong>{h[i]}.</strong> {d[i]}.</li>" for h, d in services)
        out.append(f'''<h2>{bg_h2[i]}</h2>
<p>{bg[0][i]}</p>
<p>{bg[1][i]}</p>
<p>{bg[2][i]}</p>
<h2>{("What I do", "מה אני עושה")[i]}</h2>
<p>{statement[i]}</p>
<p>{how[i]}</p>
<ul>{li}</ul>
<h2>{("Where I work", "איפה אני עובדת")[i]}</h2>
<p>{where[i]}</p>
<h2>{("For partners", "לשותפים")[i]}</h2>
<p>{des["lead_" + lang]} {link(des, lang)}.</p>
<p>{credit[i]} {link(bro, lang)}.</p>
<p>{link(adv, lang)}.</p>''')
    return out


def about_links(pages):
    """Where to go from /about/: the advisory pages, the pages for one kind of client, the places, projects, contact."""
    adv = [p for p in pages if p["section"] in ("advisory", "guide")]
    rows = [
        (("Art advisory", "ייעוץ אמנות"), [("/advisory/", "Art advisory", "ייעוץ אמנות")]
         + [(f'/{p["path"].strip("/")}/', p["title_en"], p["title_he"]) for p in adv]),
        (("Who I work with", "עם מי אני עובדת"), sc.WHO_I_WORK_WITH),
        (("Where I work", "איפה אני עובדת"), ABOUT_PLACES),
        (("Projects", "פרויקטים"), [("/projects/", "Projects", "פרויקטים"), ("/contact/", "Contact", "יצירת קשר")]),
    ]
    html = ""
    for (h_en, h_he), links in rows:
        a = "".join(f'<a href="{u}">{T(H.escape(en), H.escape(he))}</a>' for u, en, he in links)
        html += f'''
<section class="section wrap tight">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T(h_en, h_he)}</p></div></div>
  <div class="readnext who-row reveal">{a}</div>
</section>'''
    return html


def render_about(pages):
    url = f"{SITE}/{ABOUT['path']}/"
    src, w, h, alt_en, alt_he = ABOUT["portrait"]
    body_en, body_he = about_body(pages)
    tel = f'<a href="{sc.PHONE_TEL}" data-loc="about" dir="ltr">{sc.PHONE}</a>'
    mail = f'<a href="{MAIL}" data-loc="about" dir="ltr">{sc.EMAIL}</a>'
    lead_en = ("THEODORA is an art curation and advisory practice, founded and run by Stav Theodor, an art curator and advisor. "
               "THEODORA is based in Tenafly, New Jersey, and serves Tenafly, Bergen County, New Jersey and New York City, with projects in Tel Aviv. "
               "It works with private homes, interior designers and architects, private collectors, law firms, investment firms, "
               f"wealth managers, medical practices, restaurants and boutique hotels. To reach Stav, call {tel} or email {mail}.")
    lead_he = ("THEODORA היא פרקטיקה של אוצרות וייעוץ אמנות, שייסדה ומנהלת סתיו תאודור, אוצרת ויועצת אמנות. "
               "THEODORA מבוססת בטנפליי, ניו ג'רזי, ומשרתת את טנפליי, מחוז ברגן, ניו ג'רזי וניו יורק, עם פרויקטים בתל אביב. "
               "היא עובדת עם בתים פרטיים, מעצבי פנים ואדריכלים, אספנים פרטיים, משרדי עורכי דין, חברות השקעה, "
               f"מנהלי הון, מרפאות, מסעדות ומלונות בוטיק. ליצירת קשר עם סתיו: התקשרו ל-{tel} או כתבו ל-{mail}.")
    ld = [{"@type": "AboutPage", "@id": url + "#page", "url": url, "name": ABOUT["title"], "description": ABOUT["description"],
           "inLanguage": ["en", "he"], "isPartOf": {"@id": SITE + "/#site"},
           "mainEntity": [{"@id": SITE + "/#org"}, {"@id": SITE + "/#stav"}], "about": {"@id": SITE + "/#org"},
           "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + src}},
          {"@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "About", "item": url}]}]
    body = f'''
<header class="phead">
  <p class="eyebrow">{T('About', 'אודות')}</p>
  <h1 class="serif">{T(*ABOUT["h1"])}</h1>
  <p class="lead">{T(lead_en, lead_he)}</p>
  <figure class="pfig reveal" style="max-width: {w}px;">
    <img src="{src}" {sc.img_alt(alt_en, alt_he)} width="{w}" height="{h}" loading="eager" fetchpriority="high" decoding="async">
  </figure>
</header>

<section class="section wrap tight">
  <div class="prose" data-l="he" dir="rtl">
{body_he}
  </div>
  <div class="prose" data-l="en">
{body_en}
  </div>
</section>
{about_links(pages)}
<section class="section wrap tight">
  <div class="cta reveal">
    <h2 class="serif">{T(CTA_EN, CTA_HE)}</h2>
    <a class="btn" href="{MAIL}">{T('Write to Stav', 'כתבו לסתיו')}</a>
    {sc.phone_link('cta')}
    <a class="arrow" href="/contact/"><span class="ln"></span>{T("All the ways to reach me", "כל הדרכים ליצור איתי קשר")}</a>
  </div>
</section>
'''
    return (sc.head(ABOUT["title"], ABOUT["description"], url, og_image=SITE + src, lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail())


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
        else:  # the advisory hub: the two local landing pages first, the town and county pages, then the advisory pages
            sec_pages = [p for p in pages if p["section"] == "local"] + [p for p in pages if p["section"] == "area"] + [p for p in pages if p["section"] == sec]
        sec_pages = [p for p in sec_pages if not check(p, "")]
        if not sec_pages: continue
        sc.write(os.path.join(sec, "index.html"), render_hub(sec, te, th, le, lh, sec_pages, hero_src, hero_alt))
        print(f"  wrote {sec}/index.html ({len(sec_pages)} cards)")
    if "--no-sitemap" not in sys.argv:
        subprocess.run([sys.executable, "build-post-pages.py"], check=True)
    if problems: sys.exit(1)


if __name__ == "__main__":
    main()
