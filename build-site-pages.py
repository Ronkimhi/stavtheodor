#!/usr/bin/env python3
"""
Renders content/pages/*.json into standalone bilingual pages at /<path>/index.html
(advisory, projects, partners, guide), plus hub pages /advisory/ and /projects/.
Reuses the homepage's <style>, entity JSON-LD, nav, footer and language toggle so
the pages look and behave like the rest of the site. Then runs build-post-pages.py,
which owns sitemap.xml and includes these pages. Idempotent. Run from repo root.
"""
import glob, json, os, re, sys, html as H, subprocess

SITE = "https://stavtheodor.com"
src = open("index.html", encoding="utf-8", newline="").read()
style_block = re.search(r"<style>.*?</style>", src, re.S).group(0)
entity_graph = re.search(r'<!-- Structured data: Person \+ Organization \+ WebSite \(JSON-LD\) -->\r?\n<script type="application/ld\+json">.*?</script>', src, re.S).group(0)
sys.path.insert(0, ".")
import importlib.util
spec = importlib.util.spec_from_file_location("bpp_consts", "build-post-pages.py")
# Pull the shared fragments without executing the whole post builder: read them by regex.
bpp = open("build-post-pages.py", encoding="utf-8").read()
def frag(name):
    m = re.search(name + r' = """(.*?)"""', bpp, re.S)
    return m.group(1)
FAVICONS, LANG_TOGGLE, LANG_BOOT, MAIL_UI, LANG_JS, GA, FOOTER = (frag(n) for n in ["FAVICONS", "LANG_TOGGLE", "LANG_BOOT", "MAIL_UI", "LANG_JS", "GA_SNIPPET", "FOOTER"])

EXTRA_CSS = """<style>
  .page { max-width: 760px; margin: 0 auto; padding: 8px 20px 0; }
  .page .kicker { font-family: 'Cormorant Garamond', serif; font-size: 13px; letter-spacing: 0.22em; text-transform: uppercase; color: var(--bronze); margin-bottom: 14px; }
  .page h1 { font-family: 'Cormorant Garamond', serif; font-weight: 500; font-size: clamp(34px, 5vw, 52px); line-height: 1.08; margin: 0 0 18px; }
  .page h1[lang="he"] { font-family: 'Frank Ruhl Libre', serif; direction: rtl; text-align: right; display: none; }
  body.lang-en .page h1[lang="he"] { display: none; }
  body:not(.lang-en) .page h1[lang="he"] { display: block; }
  body:not(.lang-en) .page h1[lang="en"] { display: none; }
  .page .lead { font-family: 'Cormorant Garamond', serif; font-size: 22px; line-height: 1.5; color: var(--ink-soft); margin: 0 0 28px; }
  .page .lead[lang="he"] { font-family: 'Frank Ruhl Libre', serif; direction: rtl; text-align: right; font-size: 19px; }
  body.lang-en .page .lead[lang="he"] { display: none; }
  body:not(.lang-en) .page .lead[lang="en"] { display: none; }
  .page figure.hero { margin: 0 0 32px; }
  .page figure.hero img { width: 100%; height: auto; border: 1px solid var(--hairline); background: var(--ivory); padding: 0; }
  .page figure.hero figcaption { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 15px; color: var(--ink-soft); margin-top: 10px; text-align: center; }
  .page .post-body h2 { font-family: 'Cormorant Garamond', serif; font-weight: 500; font-size: 28px; line-height: 1.15; margin: 36px 0 12px; }
  .page .post-body h3 { font-family: 'Cormorant Garamond', serif; font-weight: 500; font-size: 22px; margin: 28px 0 8px; }
  .page .post-body ul, .page .post-body ol { margin: 0 0 1.2em; padding-inline-start: 1.4em; }
  .page .post-body li { margin-bottom: 0.5em; }
  .page .post-body blockquote { margin: 1.4em 0; padding-inline-start: 18px; border-inline-start: 2px solid var(--bronze); font-style: italic; color: var(--ink-soft); }
  .page .post-body figure { margin: 28px 0; }
  .page .post-body figure img { width: 100%; height: auto; border: 1px solid var(--hairline); background: var(--ivory); padding: 0; max-width: 100%; }
  .page .post-body figcaption { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 15px; color: var(--ink-soft); margin-top: 8px; text-align: center; direction: ltr; }
  .page .post-body[lang="he"] figcaption { direction: rtl; }
  .faq { margin-top: 44px; border-top: 1px solid var(--hairline); padding-top: 28px; }
  .faq h2 { font-family: 'Cormorant Garamond', serif; font-weight: 500; font-size: 26px; margin: 0 0 16px; }
  .faq details { border-bottom: 1px solid var(--hairline); padding: 12px 0; }
  .faq summary { cursor: pointer; font-family: 'Cormorant Garamond', serif; font-size: 20px; font-weight: 500; list-style: none; }
  .faq summary::-webkit-details-marker { display: none; }
  .faq details p { margin-top: 10px; font-size: 16.5px; line-height: 1.6; color: var(--ink-soft); }
  .faq[lang="he"] { direction: rtl; text-align: right; font-family: 'Frank Ruhl Libre', serif; }
  .faq[lang="he"] summary, .faq[lang="he"] h2 { font-family: 'Frank Ruhl Libre', serif; }
  body.lang-en .faq[lang="he"] { display: none; }
  body:not(.lang-en) .faq[lang="en"] { display: none; }
  .cta-card { margin: 48px 0 0; padding: 28px 30px; background: rgba(160,129,92,0.08); border-left: 3px solid var(--bronze); }
  .cta-card p { font-family: 'Cormorant Garamond', serif; font-size: 21px; line-height: 1.45; margin: 0 0 14px; }
  .cta-card[lang="he"] { direction: rtl; text-align: right; border-left: 0; border-right: 3px solid var(--bronze); }
  .cta-card[lang="he"] p { font-family: 'Frank Ruhl Libre', serif; font-size: 18px; }
  body.lang-en .cta-card[lang="he"] { display: none; }
  body:not(.lang-en) .cta-card[lang="en"] { display: none; }
  .cta-card a.btn { display: inline-block; font-family: 'Cormorant Garamond', serif; font-size: 15px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ivory); background: var(--bronze); padding: 12px 22px; text-decoration: none; }
  .related { margin-top: 44px; border-top: 1px solid var(--hairline); padding-top: 24px; }
  .related ul { list-style: none; padding: 0; margin: 12px 0 0; line-height: 2; }
  .hub { max-width: 1040px; margin: 0 auto; padding: 0 20px; }
  .hub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 28px; margin-top: 28px; }
  .hub-card { display: block; text-decoration: none; color: var(--ink); border: 1px solid var(--hairline); background: var(--ivory); }
  .hub-card img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; display: block; }
  .hub-card .in { padding: 16px 18px 20px; }
  .hub-card h3 { font-family: 'Cormorant Garamond', serif; font-weight: 500; font-size: 22px; line-height: 1.15; margin: 0 0 8px; }
  .hub-card p { font-size: 15px; color: var(--ink-soft); line-height: 1.5; margin: 0; }
  .hub-card:hover { border-color: var(--bronze); }
</style>"""

NAV = """<nav>
  <a href="/"><span data-l="en">Home</span><span data-l="he">דף הבית</span></a>
  <a href="/advisory/"><span data-l="en">Advisory</span><span data-l="he">ייעוץ</span></a>
  <a href="/projects/"><span data-l="en">Projects</span><span data-l="he">פרויקטים</span></a>
  <a href="/#radar"><span data-l="en">Art Radar</span><span data-l="he">ראדאר אמנות</span></a>
  <a href="/#contact"><span data-l="en">Contact</span><span data-l="he">יצירת קשר</span></a>
</nav>

<header class="hero wrap" style="padding: 56px 24px 32px;">
  <a href="/" style="text-decoration:none; display:inline-block;">
    <img class="hero-logo" src="/images/theodora-logo.png" alt="THEODORA &middot; fine art living" width="440" height="195" style="width:150px; height:auto;">
  </a>
</header>

<hr class="divider">"""

def head(title, desc, url, og_image, ld_blocks):
    ld = "\n".join(f'<script type="application/ld+json">\n{json.dumps(b, ensure_ascii=False, indent=2)}\n</script>' for b in ld_blocks)
    return f"""<!DOCTYPE html>
<html lang="he" data-default-lang="he">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{H.escape(title)} &middot; THEODORA</title>
{FAVICONS}
<meta name="description" content="{H.escape(desc, quote=True)}">
<meta property="og:title" content="{H.escape(title, quote=True)}">
<meta property="og:description" content="{H.escape(desc, quote=True)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="THEODORA">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="he_IL">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{H.escape(title, quote=True)}">
<meta name="twitter:description" content="{H.escape(desc, quote=True)}">
<meta name="twitter:image" content="{og_image}">
<link rel="canonical" href="{url}">
{style_block}
{EXTRA_CSS}
{ld}
{entity_graph}
</head>
<body>

{LANG_BOOT}

{LANG_TOGGLE}

{NAV}
"""

def tail():
    return f"""
<hr class="divider">

{FOOTER}

{MAIL_UI}

{GA}

{LANG_JS}

</body>
</html>
"""

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
        pages.append(p)
    return pages

def render_page(p, all_pages):
    url = f"{SITE}/{p['path'].strip('/')}/"
    og = SITE + (p.get("og_image") or (p.get("hero_image") or {}).get("src") or "/og-image.jpg")
    kicker = p.get("kicker", {"advisory": "Art advisory", "projects": "Project", "partners": "Working together", "guide": "Guide"}.get(p["section"], "THEODORA"))
    kicker_he = p.get("kicker_he", {
        "Art advisory": "ייעוץ אמנות", "Project": "פרויקט", "Working together": "עבודה משותפת",
        "Guide": "מדריך", "For partners": "לשותפים", "THEODORA": "THEODORA",
    }.get(kicker, {"advisory": "ייעוץ אמנות", "projects": "פרויקט", "partners": "עבודה משותפת", "guide": "מדריך"}.get(p["section"], "THEODORA")))
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

    hero = ""
    hi = p.get("hero_image")
    if hi:
        cap = ""
        if hi.get("caption_en"):
            cap += '<figcaption data-l="en">' + H.escape(hi["caption_en"]) + "</figcaption>\n    "
        if hi.get("caption_he"):
            cap += '<figcaption data-l="he" dir="rtl">' + H.escape(hi["caption_he"]) + "</figcaption>"
        hero = f"""  <figure class="hero">
    <img src="{hi['src']}" alt="{H.escape(hi.get('alt_en',''), quote=True)}" loading="eager">
    {cap}
  </figure>
"""
    faq_html = ""
    if p.get("faq"):
        en = "\n".join(f'    <details><summary>{H.escape(q["q_en"])}</summary><p>{q["a_en"]}</p></details>' for q in p["faq"])
        he = "\n".join(f'    <details><summary>{H.escape(q["q_he"])}</summary><p>{q["a_he"]}</p></details>' for q in p["faq"])
        faq_html = f"""  <section class="faq" lang="en">
    <h2>Questions people ask</h2>
{en}
  </section>
  <section class="faq" lang="he" dir="rtl">
    <h2>שאלות נפוצות</h2>
{he}
  </section>
"""
    cta_en = p.get("cta_en") or "Send me one photo of the wall, and a line about the space. I will tell you what I see."
    cta_he = p.get("cta_he") or "שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה."
    mail = "mailto:stav@stavtheodor.com"
    related = ""
    rel = [r for r in p.get("related", []) if any(o["path"].strip("/") == r.strip("/") for o in all_pages)]
    if rel:
        items = []
        for r in rel:
            o = next(o for o in all_pages if o["path"].strip("/") == r.strip("/"))
            items.append(f'      <li><a href="/{o["path"].strip("/")}/"><span data-l="en">{H.escape(o["title_en"])}</span><span data-l="he" dir="rtl">{H.escape(o.get("title_he") or o["title_en"])}</span></a></li>')
        related = f"""  <section class="related">
    <div class="label" data-l="en" style="text-align:left;">Read next</div>
    <div class="label" data-l="he" dir="rtl" style="text-align:right;">להמשך קריאה</div>
    <ul>
{chr(10).join(items)}
    </ul>
  </section>
"""
    body = f"""
<section class="page">
  <div class="kicker" data-l="en">{H.escape(kicker)}</div>
  <div class="kicker" data-l="he" dir="rtl">{H.escape(kicker_he)}</div>
  <h1 lang="en">{H.escape(p['title_en'])}</h1>
  <h1 lang="he" dir="rtl">{H.escape(p['title_he'])}</h1>
  <p class="lead" lang="en">{p['lead_en']}</p>
  <p class="lead" lang="he" dir="rtl">{p['lead_he']}</p>
{hero}  <div class="post-body" lang="he" dir="rtl">
{p['body_he']}
  </div>
  <div class="post-body post-body-en" lang="en" dir="ltr">
{p['body_en']}
  </div>
{faq_html}  <div class="cta-card" lang="en">
    <p>{cta_en}</p>
    <a class="btn" href="{mail}">Write to Stav</a>
  </div>
  <div class="cta-card" lang="he" dir="rtl">
    <p>{cta_he}</p>
    <a class="btn" href="{mail}">כתבו לסתיו</a>
  </div>
{related}</section>
"""
    return head(p["title_en"], p["meta_description"], url, og, ld) + body + tail()

def render_hub(section, title_en, title_he, lead_en, lead_he, pages):
    url = f"{SITE}/{section}/"
    cards = []
    for p in pages:
        img = (p.get("hero_image") or {}).get("src") or p.get("og_image") or "/og-image.jpg"
        cards.append(f"""    <a class="hub-card" href="/{p['path'].strip('/')}/">
      <img src="{img}" alt="{H.escape((p.get('hero_image') or {}).get('alt_en', p['title_en']), quote=True)}" loading="lazy">
      <div class="in"><h3 data-l="en">{H.escape(p['title_en'])}</h3><h3 data-l="he" dir="rtl">{H.escape(p.get('title_he') or p['title_en'])}</h3><p data-l="en">{H.escape(strip_tags(p['meta_description']))}</p><p data-l="he" dir="rtl">{H.escape(snippet(p.get('lead_he') or ''))}</p></div>
    </a>""")
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title_en, "url": url, "inLanguage": ["en", "he"],
           "hasPart": [{"@type": "WebPage", "name": p["title_en"], "url": f"{SITE}/{p['path'].strip('/')}/"} for p in pages]}]
    body = f"""
<section class="hub">
  <div class="page" style="max-width: 760px; padding: 0;">
    <h1 lang="en">{H.escape(title_en)}</h1>
    <h1 lang="he" dir="rtl">{H.escape(title_he)}</h1>
    <p class="lead" lang="en">{lead_en}</p>
    <p class="lead" lang="he" dir="rtl">{lead_he}</p>
  </div>
  <div class="hub-grid">
{chr(10).join(cards)}
  </div>
  <div class="page" style="max-width: 760px;">
    <div class="cta-card" lang="en"><p>Send me one photo of the wall, and a line about the space. I will tell you what I see.</p><a class="btn" href="mailto:stav@stavtheodor.com">Write to Stav</a></div>
    <div class="cta-card" lang="he" dir="rtl"><p>שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה.</p><a class="btn" href="mailto:stav@stavtheodor.com">כתבו לסתיו</a></div>
  </div>
</section>
"""
    desc = strip_tags(lead_en)[:158]
    return head(title_en, desc, url, SITE + "/og-image.jpg", ld) + body + tail()

def check(p, out):
    bad = []
    if re.search(r"[—–]", out): bad.append("em/en dash")
    if re.search(r"\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1 ?\(?\d{3}", out): bad.append("phone number")
    for k in ["title_en", "title_he", "lead_en", "lead_he", "body_en", "body_he", "meta_description"]:
        if not p.get(k): bad.append(f"missing {k}")
    return bad

def main():
    pages = load_pages()
    problems = 0
    for p in pages:
        out = render_page(p, pages).replace("\r\n", "\n")
        bad = check(p, out)
        if bad:
            print(f"  BLOCKED {p['path']}: {', '.join(bad)}"); problems += 1; continue
        d = p["path"].strip("/")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n").write(out)
        print(f"  wrote {d}/index.html")
    hubs = {
        "advisory": ("Art advisory, answered plainly", "ייעוץ אמנות, בשפה פשוטה",
                     "What an art advisor does, what it costs, and how the work goes from a first conversation to a piece on the wall. Written for people who are about to buy, build, or move.",
                     "מה יועצת אמנות עושה, כמה זה עולה, ואיך התהליך מתקדם משיחה ראשונה ועד יצירה על הקיר. נכתב לאנשים שעומדים לקנות, לבנות או לעבור דירה."),
        "projects": ("Projects", "פרויקטים",
                     "Homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels from Chengdu to Amman, and one exhibition that reached Geneva. Each page tells what the space asked for and what answered it.",
                     "בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות מצ'נגדו ועד עמאן, ותערוכה אחת שהגיעה לז'נבה. כל עמוד מספר מה החלל ביקש ומה ענה לו."),
    }
    for sec, (te, th, le, lh) in hubs.items():
        sec_pages = [p for p in pages if p["section"] == sec and not check(p, render_page(p, pages))]
        if not sec_pages: continue
        os.makedirs(sec, exist_ok=True)
        open(os.path.join(sec, "index.html"), "w", encoding="utf-8", newline="\n").write(render_hub(sec, te, th, le, lh, sec_pages))
        print(f"  wrote {sec}/index.html ({len(sec_pages)} cards)")
    if "--no-sitemap" not in sys.argv:
        subprocess.run([sys.executable, "build-post-pages.py"], check=True)
    if problems: sys.exit(1)

if __name__ == "__main__":
    main()
