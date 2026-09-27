#!/usr/bin/env python3
"""
Renders content/pages/*.json into standalone bilingual pages at /<path>/index.html
(advisory, projects, partners, guide), plus the hub pages /advisory/ and /projects/,
in the site's one theme (css/theme.css) with the shared chrome (site_chrome.py).
Then runs build-post-pages.py, which owns sitemap.xml and includes these pages.
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
SECTION_KICKER = {"advisory": "Art advisory", "projects": "Project", "partners": "Working together", "guide": "Guide"}
SECTION_KICKER_HE = {"advisory": "ייעוץ אמנות", "projects": "פרויקט", "partners": "עבודה משותפת", "guide": "מדריך"}
CTA_EN = "Send me one photo of the wall, and a line about the space. I will tell you what I see."
CTA_HE = "שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה."
MAIL = f"mailto:{sc.EMAIL}"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


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


def ld_blocks(p, url, og):
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
        "author": {"@type": "Person", "name": "Stav Theodor-Kimhi", "url": SITE + "/"},
        "publisher": {"@type": "Organization", "name": "THEODORA", "url": SITE + "/"},
    }
    if p.get("schema_type") == "Service":
        main.update({"provider": {"@type": "Organization", "name": "THEODORA", "url": SITE + "/"}, "areaServed": ["New York City", "New Jersey", "Tel Aviv"], "serviceType": p.get("service_type", "Art advisory")})
    main.update(p.get("schema_extra", {}))
    ld = [main, {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": {"advisory": "Advisory", "projects": "Projects", "partners": "Working together", "guide": "Guides"}.get(p["section"], "Pages"), "item": SITE + "/" + ({"advisory": "advisory", "projects": "projects"}.get(p["section"], p["path"].split("/")[0])) + "/"},
            {"@type": "ListItem", "position": 3, "name": p["title_en"], "item": url},
        ]}]
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


def cta_html(p):
    cta_en = p.get("cta_en") or CTA_EN
    cta_he = p.get("cta_he") or CTA_HE
    return f'''
  <div class="cta reveal">
    <h2 class="serif">{T(cta_en, cta_he)}</h2>
    <a class="btn" href="{MAIL}">{T('Write to Stav', 'כתבו לסתיו')}</a>
  </div>'''


def render_article_page(p, all_pages):
    """Advisory, partner and guide pages: text header, optional photo, the reading column.
    English opens by default (site owner, 2026-09-26); the Hebrew twin sits behind the switch."""
    url = f"{SITE}/{p['path'].strip('/')}/"
    og = SITE + (p.get("og_image") or (p.get("hero_image") or {}).get("src") or "/og-image.jpg")
    kicker, kicker_he = kickers(p)
    hero = ""
    hi = p.get("hero_image")
    if hi:
        cap = ""
        if hi.get("caption_en") or hi.get("caption_he"):
            cap = f'\n    <figcaption>{T(H.escape(hi.get("caption_en", "")), H.escape(hi.get("caption_he", "")))}</figcaption>'
        hero = f'''
  <figure class="pfig reveal">
    <img src="{hi['src']}" alt="{H.escape(hi.get('alt_en', ''), quote=True)}" loading="eager">{cap}
  </figure>'''
    body = f'''
<header class="phead">
  <p class="eyebrow">{T(H.escape(kicker), H.escape(kicker_he))}</p>
  <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
  <p class="lead">{T(p['lead_en'], p['lead_he'])}</p>{hero}
</header>

<section class="section wrap tight">
  <div class="prose" data-l="he" dir="rtl">
{p['body_he']}
  </div>
  <div class="prose" data-l="en">
{p['body_en']}
  </div>
</section>
{faq_html(p)}
<section class="section wrap tight">{cta_html(p)}
  {related_html(p, all_pages)}
</section>
'''
    return (sc.head(f"{p['title_en']} · THEODORA", p["meta_description"], url, og_image=og, og_type="article",
                    lang="en", ld=ld_blocks(p, url, og))
            + sc.body_open() + sc.nav() + body + sc.tail())


def render_project_page(p, all_pages, projects):
    """A project: full-bleed hero, one serif lead, the story, three more projects, the next one."""
    url = f"{SITE}/{p['path'].strip('/')}/"
    hero = p["hero_image"]
    og = SITE + (p.get("og_image") or hero["src"])
    kicker, kicker_he = kickers(p)
    i = projects.index(p)
    nxt = projects[(i + 1) % len(projects)]
    more = [projects[(i + j) % len(projects)] for j in (1, 2, 3)]
    body = f'''
<header class="phero">
  <img src="{hero['src']}" alt="{H.escape(hero.get('alt_en', ''), quote=True)}" fetchpriority="high">
  <div class="scrim"></div>
  <div class="title">
    <p class="eyebrow">{T('Projects · ' + H.escape(kicker), 'פרויקטים · ' + H.escape(kicker_he))}</p>
    <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
    <p class="cap">{T(H.escape(hero.get('caption_en', '')), H.escape(hero.get('caption_he', '')))}</p>
  </div>
</header>

<section class="plead"><p class="reveal">{T(p['lead_en'], p['lead_he'])}</p></section>

<section class="section wrap">
  <div class="prose" data-l="he" dir="rtl">
{p['body_he']}
  </div>
  <div class="prose" data-l="en">
{p['body_en']}
  </div>
</section>
{faq_html(p)}
<section class="section wrap">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('More projects', 'עוד פרויקטים')}</p></div><a class="arrow" href="/projects/"><span class="ln"></span>{T('All projects', 'כל הפרויקטים')}</a></div>
  <div class="grid3">{''.join(sc.project_card(q) for q in more)}
  </div>
  <div class="next reveal">
    <p class="eyebrow">{T('Next project', 'הפרויקט הבא')}</p>
    <a class="big" href="/{nxt['path'].strip('/')}/">{T(H.escape(nxt['title_en']), H.escape(nxt['title_he']))}</a>
    {related_html(p, all_pages, exclude_projects=True)}
  </div>
</section>
'''
    return (sc.head(f"{p['title_en']} · THEODORA", p["meta_description"], url, og_image=og, og_type="article",
                    lang="en", ld=ld_blocks(p, url, og))
            + sc.body_open() + sc.nav() + body + sc.tail())


def render_hub(section, title_en, title_he, lead_en, lead_he, pages, hero_src, hero_alt):
    url = f"{SITE}/{section}/"
    cards = "".join(sc.project_card(p) if p.get("hero_image") else f'''
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

<section class="section wrap tight">
  <div class="cta reveal">
    <h2 class="serif">{T(CTA_EN, CTA_HE)}</h2>
    <a class="btn" href="{MAIL}">{T('Write to Stav', 'כתבו לסתיו')}</a>
  </div>
</section>
'''
    desc = strip_tags(lead_en)[:158]
    return (sc.head(f"{title_en} · THEODORA", desc, url, og_image=SITE + hero_src, lang="en", ld=ld)
            + sc.body_open() + sc.nav() + body + sc.tail())


def check(p, out):
    bad = []
    if re.search("[\u2013\u2014]", out): bad.append("em/en dash")
    if re.search(r"\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1 ?\(?\d{3}", out): bad.append("phone number")
    for k in ["title_en", "title_he", "lead_en", "lead_he", "body_en", "body_he", "meta_description"]:
        if not p.get(k): bad.append(f"missing {k}")
    if p["section"] == "projects" and not p.get("hero_image"): bad.append("project page without hero_image")
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
    for sec, (te, th, le, lh, hero_src, hero_alt) in HUBS.items():
        sec_pages = projects if sec == "projects" else [p for p in pages if p["section"] == sec]
        sec_pages = [p for p in sec_pages if not check(p, "")]
        if not sec_pages: continue
        sc.write(os.path.join(sec, "index.html"), render_hub(sec, te, th, le, lh, sec_pages, hero_src, hero_alt))
        print(f"  wrote {sec}/index.html ({len(sec_pages)} cards)")
    if "--no-sitemap" not in sys.argv:
        subprocess.run([sys.executable, "build-post-pages.py"], check=True)
    if problems: sys.exit(1)


if __name__ == "__main__":
    main()
