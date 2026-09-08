#!/usr/bin/env python3
"""
Generates a real, standalone, indexable URL for every Art Radar post
(radar/<slug>/index.html) from the single index.html source of truth,
and refreshes sitemap.xml to list every post URL.

Run this after adding a new post block to index.html, before deploying.
The homepage itself (index.html) is never restructured. The only thing it
rewrites inside index.html is each post's JSON-LD `url` / `mainEntityOfPage`
(fragment -> real URL). No visible "Permalink" link is added to posts: the
site owner removed those on 2026-07-02 (they looked odd in the timeline).
The /radar/<slug>/ pages still exist for SEO and LLM discoverability; they
are simply not linked from each post's card.

Everything else on the homepage (layout, content, styling) is untouched.
"""
import re
import json
import os

SITE = "https://stavtheodor.com"
SRC = "index.html"
OUT_DIR = "radar"

html = open(SRC, encoding="utf-8", newline="").read()

style_block = re.search(r"<style>.*?</style>", html, re.S).group(0)

entity_graph_script = re.search(
    r'<!-- Structured data: Person \+ Organization \+ WebSite \(JSON-LD\) -->\r?\n<script type="application/ld\+json">.*?</script>',
    html, re.S,
).group(0)

FAVICONS = """<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Frank+Ruhl+Libre:wght@300;400;500&display=swap" rel="stylesheet">"""

LANG_TOGGLE = """<div class="lang-bar">
  <div class="lang-switch" role="group" aria-label="Choose language / בחירת שפה">
    <button type="button" data-lang="he" aria-pressed="false">עברית</button>
    <button type="button" data-lang="en" aria-pressed="false">English</button>
  </div>
</div>"""

LANG_BOOT = """<script>
/* Resolve the language before anything paints. A stored choice is global and wins
   everywhere; with no stored choice each page falls back to its own data-default-lang,
   so first-time visitors see exactly what they saw before the switcher existed. */
(function () {
  var def = document.documentElement.getAttribute('data-default-lang') || 'en';
  var lang = def;
  try { lang = localStorage.getItem('radarLang') || def; } catch (e) {}
  if (lang !== 'he' && lang !== 'en') { lang = def; }
  document.body.classList.toggle('lang-en', lang === 'en');
  document.body.classList.toggle('lang-he', lang === 'he');
  document.documentElement.lang = lang;
})();
</script>"""

MAIL_UI = """<div class="mail-fallback" id="mail-fallback" role="dialog" aria-modal="true" aria-labelledby="mail-fallback-title">
  <div class="card">
    <h3 id="mail-fallback-title"><span data-l="en">Write to Stav</span><span data-l="he">כתבו לסתיו</span></h3>
    <p><span data-l="en">This browser has no email app set up, so nothing opened. Copy the address, or open it in your webmail.</span><span data-l="he">בדפדפן הזה לא מוגדרת תוכנת דואר, ולכן לא נפתח כלום. העתיקו את הכתובת, או פתחו אותה בדואר האינטרנטי שלכם.</span></p>
    <a class="addr" id="mail-fallback-addr" href="mailto:stav@stavtheodor.com">stav@stavtheodor.com</a>
    <div class="row">
      <button type="button" id="mail-fallback-copy"><span data-l="en">Copy</span><span data-l="he">העתקה</span></button>
      <a class="solid" id="mail-fallback-gmail" href="https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=stav@stavtheodor.com" target="_blank" rel="noopener">Gmail</a>
      <a id="mail-fallback-outlook" href="https://outlook.live.com/mail/0/deeplink/compose?to=stav@stavtheodor.com" target="_blank" rel="noopener">Outlook</a>
    </div>
    <button type="button" class="close"><span data-l="en">Close</span><span data-l="he">סגירה</span></button>
  </div>
</div>"""

LANG_JS = """<script>
(function () {
  var KEY = 'radarLang';

  function apply(lang) {
    document.body.classList.toggle('lang-en', lang === 'en');
    document.body.classList.toggle('lang-he', lang === 'he');
    document.documentElement.lang = lang;
    document.querySelectorAll('.lang-switch button').forEach(function (b) {
      var on = b.getAttribute('data-lang') === lang;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  apply(document.body.classList.contains('lang-he') ? 'he' : 'en');

  document.querySelectorAll('.lang-switch button').forEach(function (b) {
    b.addEventListener('click', function () {
      var lang = b.getAttribute('data-lang');
      try { localStorage.setItem(KEY, lang); } catch (e) {}
      apply(lang);
    });
  });

  /* A mailto: link does nothing at all in a browser with no mail handler registered,
     which is why the Write to Stav button felt dead. Keep the mailto (it is correct
     and works on phones and with a real mail client), and if the click was swallowed,
     offer the address, a copy button and webmail compose links instead. */
  var panel = document.getElementById('mail-fallback');
  if (!panel) { return; }
  var addrEl = document.getElementById('mail-fallback-addr');
  var gmail = document.getElementById('mail-fallback-gmail');
  var outlook = document.getElementById('mail-fallback-outlook');
  var copyBtn = document.getElementById('mail-fallback-copy');

  function closePanel() { panel.classList.remove('open'); }

  function openPanel(addr) {
    addrEl.textContent = addr;
    addrEl.setAttribute('href', 'mailto:' + addr);
    gmail.setAttribute('href', 'https://mail.google.com/mail/?view=cm&fs=1&to=' + encodeURIComponent(addr));
    outlook.setAttribute('href', 'https://outlook.live.com/mail/0/deeplink/compose?to=' + encodeURIComponent(addr));
    panel.classList.add('open');
  }

  panel.addEventListener('click', function (e) {
    if (e.target === panel || e.target.classList.contains('close') || (e.target.parentNode && e.target.parentNode.classList && e.target.parentNode.classList.contains('close'))) {
      closePanel();
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closePanel(); }
  });
  copyBtn.addEventListener('click', function () {
    var addr = addrEl.textContent;
    var done = function () {
      var spans = copyBtn.querySelectorAll('span');
      var was = [];
      spans.forEach(function (s, i) { was[i] = s.textContent; });
      spans.forEach(function (s) { s.textContent = s.getAttribute('data-l') === 'he' ? 'הועתק' : 'Copied'; });
      setTimeout(function () { spans.forEach(function (s, i) { s.textContent = was[i]; }); }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(addr).then(done, function () {});
    } else {
      var t = document.createElement('textarea');
      t.value = addr; document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); done(); } catch (e) {}
      document.body.removeChild(t);
    }
  });

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href^="mailto:"]') : null;
    if (!a || a === addrEl) { return; }
    var addr = a.getAttribute('href').slice(7).split('?')[0];
    var handled = false;
    function mark() { handled = true; }
    window.addEventListener('blur', mark);
    document.addEventListener('visibilitychange', mark);
    setTimeout(function () {
      window.removeEventListener('blur', mark);
      document.removeEventListener('visibilitychange', mark);
      if (handled) { return; }
      openPanel(addr);
    }, 1000);
  });
})();
</script>"""

GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4300MN0Q97"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-4300MN0Q97');
</script>"""

FOOTER = """<footer id="contact">
  <div class="wrap">
    <div class="name" data-l="en">Stav Theodor&#8209;Kimhi</div>
    <div class="name" data-l="he" dir="rtl">סתיו תאודור&#8209;קמחי</div>
    <div class="sub" data-l="en">Art Curation &amp; Advisory &middot; Tenafly, New Jersey</div>
    <div class="sub" data-l="he" dir="rtl">אוצרות וייעוץ אמנות &middot; טנפליי, ניו ג'רזי</div>
    <ul class="contact-list">
      <li><a href="mailto:stav@stavtheodor.com">stav@stavtheodor.com</a></li>
      <li><a href="https://chat.whatsapp.com/CapF9HczSoL4szwUKKtkq5" target="_blank" rel="noopener"><span data-l="en">Art Radar on WhatsApp</span><span data-l="he">ראדאר אמנות בוואטסאפ</span></a></li>
      <li><a href="https://www.instagram.com/theodorafineart/" target="_blank" rel="noopener" aria-label="THEODORA on Instagram"><svg class="ig-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/></svg><span data-l="en">Instagram</span><span data-l="he">אינסטגרם</span></a></li>
      <li><a href="/#portfolio"><span data-l="en">Portfolio</span><span data-l="he">תיק עבודות</span></a></li>
    </ul>
    <div class="copyright">&copy; 2026 THEODORA</div>
  </div>
</footer>"""

posts_section = re.search(r'<section id="posts".*?</section>', html, re.S).group(0)

pair_re = re.compile(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>\s*'
    r'<article class="(post[^"]*)" id="([a-z0-9\-]+)">(.*?)</article>',
    re.S,
)
pairs = pair_re.findall(posts_section)
if not pairs:
    raise SystemExit("No posts found — check the regex against index.html structure.")

posts = []
for json_text, article_class, slug, article_inner in pairs:
    data = json.loads(json_text)
    img_match = re.search(r'<img src="([^"]+)"', article_inner)
    og_image = f"{SITE}/{img_match.group(1)}" if img_match else f"{SITE}/og-image.jpg"
    posts.append({
        "slug": slug,
        "article_class": article_class,
        "headline": data["headline"],
        "description": data["description"],
        "datePublished": data["datePublished"],
        "dateModified": data.get("dateModified", data["datePublished"]),
        "json_text": json_text,
        "article_inner": article_inner,
        "og_image": og_image,
    })

print(f"Found {len(posts)} posts")

# ---- 1. Rewrite JSON-LD url/mainEntityOfPage in index.html to real permalinks ----
# Safe to re-run: posts already using the real permalink (from a prior run, or
# because the post was authored with the real URL directly) are left untouched.
new_html = html
for p in posts:
    frag_url = f"{SITE}/#{p['slug']}"
    real_url = f"{SITE}/radar/{p['slug']}/"
    old_json = p["json_text"]
    new_json = old_json.replace(
        f'"url": "{frag_url}"', f'"url": "{real_url}"'
    ).replace(
        f'"mainEntityOfPage": "{frag_url}"', f'"mainEntityOfPage": "{real_url}"'
    )
    if new_json != old_json:
        new_html = new_html.replace(old_json, new_json, 1)

# NOTE: this script used to inject a visible <a class="permalink"> link under each
# post's date. The site owner removed those links on 2026-07-02. Do not reintroduce
# the injection; the /radar/<slug>/ pages remain the canonical post URLs regardless.

open(SRC, "w", encoding="utf-8", newline="").write(new_html)
print("index.html updated (JSON-LD permalink URLs)")

# ---- 3. Generate radar/<slug>/index.html for every post ----
os.makedirs(OUT_DIR, exist_ok=True)

def render_post_page(p, all_posts):
    permalink = f"{SITE}/radar/{p['slug']}/"
    # Post pages live at /radar/<slug>/, so relative image paths copied from
    # index.html would resolve to /radar/<slug>/images/... and 404. Make them
    # root-relative. (Fixed 2026-07-21; every post page had broken images.)
    article_inner = p["article_inner"].replace('src="images/', 'src="/images/')
    updated_json = p["json_text"].replace(
        f'"url": "{SITE}/#{p["slug"]}"', f'"url": "{permalink}"'
    ).replace(
        f'"mainEntityOfPage": "{SITE}/#{p["slug"]}"', f'"mainEntityOfPage": "{permalink}"'
    )

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Art Radar", "item": SITE + "/#radar"},
            {"@type": "ListItem", "position": 3, "name": p["headline"], "item": permalink},
        ],
    }

    others = [o for o in all_posts if o["slug"] != p["slug"]][:8]
    more_links = "\n".join(
        f'      <li><a href="/radar/{o["slug"]}/">{o["headline"]}</a></li>' for o in others
    )

    return f"""<!DOCTYPE html>
<html lang="he" data-default-lang="he">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['headline']} &middot; Art Radar &middot; THEODORA</title>
{FAVICONS}
<meta name="description" content="{p['description']}">
<meta property="og:title" content="{p['headline']}">
<meta property="og:description" content="{p['description']}">
<meta property="og:type" content="article">
<meta property="og:url" content="{permalink}">
<meta property="og:image" content="{p['og_image']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="THEODORA">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{p['headline']}">
<meta name="twitter:description" content="{p['description']}">
<meta name="twitter:image" content="{p['og_image']}">
<link rel="canonical" href="{permalink}">
{style_block}
<script type="application/ld+json">
{updated_json}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb, indent=2)}
</script>
{entity_graph_script}
</head>
<body>

{LANG_BOOT}

{LANG_TOGGLE}

<nav>
  <a href="/"><span data-l="en">Home</span><span data-l="he">דף הבית</span></a>
  <a href="/#about"><span data-l="en">About</span><span data-l="he">אודות</span></a>
  <a href="/#radar"><span data-l="en">Art Radar</span><span data-l="he">ראדאר אמנות</span></a>
  <a href="/#contact"><span data-l="en">Contact</span><span data-l="he">יצירת קשר</span></a>
</nav>

<header class="hero wrap" style="padding: 56px 24px 40px;">
  <a href="/" style="text-decoration:none; display:inline-block;">
    <img class="hero-logo" src="/images/theodora-logo.png" alt="THEODORA &middot; fine art living" width="440" height="195" style="width:150px; height:auto;">
  </a>
</header>

<hr class="divider">

<section id="posts" class="wrap">
  <article class="{p['article_class']}" id="{p['slug']}">{article_inner}</article>
</section>

<hr class="divider">

<section class="wrap" style="padding: 40px 0 64px;">
  <div class="label" data-l="en">More from Art Radar</div>
  <div class="label" data-l="he">עוד מראדאר אמנות</div>
  <ul style="margin-top: 16px; line-height: 2;">
{more_links}
  </ul>
  <p style="margin-top: 24px;"><a href="/#radar"><span data-l="en">&larr; Full Art Radar archive</span><span data-l="he">&larr; לארכיון המלא של ראדאר אמנות</span></a></p>
</section>

<hr class="divider">

{FOOTER}

{MAIL_UI}

{GA_SNIPPET}

{LANG_JS}

</body>
</html>
"""

for p in posts:
    post_dir = os.path.join(OUT_DIR, p["slug"])
    os.makedirs(post_dir, exist_ok=True)
    out_path = os.path.join(post_dir, "index.html")
    page = render_post_page(p, posts).replace("\r\n", "\n")
    open(out_path, "w", encoding="utf-8", newline="\n").write(page)
    print(f"  wrote {out_path}")

# ---- 4. Rewrite sitemap.xml with homepage + every post URL ----
latest = max(p["dateModified"] for p in posts)
url_entries = [f"""  <url>
    <loc>{SITE}/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""", f"""  <url>
    <loc>{SITE}/museum/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>"""]

# The Museum's static, crawlable pages (generated by museum/tools/build_artist_pages.py)
import glob as _glob
museum_pages = sorted(_glob.glob("museum/artists/*/index.html"))
if os.path.exists("museum/artists/index.html"):
    url_entries.append(f"""  <url>
    <loc>{SITE}/museum/artists/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
for mp in museum_pages:
    slug = mp.replace("\\", "/").split("/")[2]  # glob uses OS separator; normalize for Windows
    url_entries.append(f"""  <url>
    <loc>{SITE}/museum/artists/{slug}/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>""")
# Growth pages generated by build-site-pages.py from content/pages/*.json (added 2026-09-04)
_content = sorted(_glob.glob("content/pages/*.json"))
_hubs = set()
for _cf in _content:
    _cp = json.load(open(_cf, encoding="utf-8"))
    _hubs.add(_cp["path"].strip("/").split("/")[0] if _cp["section"] in ("advisory", "projects") else None)
    if os.path.exists(os.path.join(_cp["path"].strip("/"), "index.html")):
        url_entries.append(f"""  <url>
    <loc>{SITE}/{_cp["path"].strip("/")}/</loc>
    <lastmod>{_cp.get("date_modified", _cp.get("date", latest))}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
for _h in sorted(h for h in _hubs if h):
    if os.path.exists(os.path.join(_h, "index.html")):
        url_entries.append(f"""  <url>
    <loc>{SITE}/{_h}/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>""")
for p in sorted(posts, key=lambda x: x["datePublished"], reverse=True):
    url_entries.append(f"""  <url>
    <loc>{SITE}/radar/{p['slug']}/</loc>
    <lastmod>{p['dateModified']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(url_entries)
    + "\n</urlset>\n"
)
open("sitemap.xml", "w", encoding="utf-8").write(sitemap)
print(f"sitemap.xml updated with {len(url_entries)} URLs")
