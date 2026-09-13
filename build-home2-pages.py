#!/usr/bin/env python3
"""Build the /2/ tree: the second homepage and its project and Art Radar pages.

Generated files (do not hand-edit them, edit this script or the content and re-run):
  2/index.html                     the homepage
  2/projects/index.html            all projects
  2/projects/<slug>/index.html     one page per project, from content/pages/*.json (section "projects")
  2/radar/index.html               every Art Radar post as a timeline, from index.html

Rules honored: every visible string has an English and a Hebrew twin behind the global
switch (radarLang); the mailto fallback panel ships on every page; no phone numbers;
no em or en dashes in English; pages are noindex until the owner promotes /2/.
"""
import glob
import html as H
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
GA_ID = 'G-4300MN0Q97'
WHATSAPP = 'https://chat.whatsapp.com/CapF9HczSoL4szwUKKtkq5'
INSTAGRAM = 'https://www.instagram.com/theodorafineart/'
EMAIL = 'stav@stavtheodor.com'


def strip_tags(s):
    return H.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or ''))).strip()


def first_sentence(s):
    s = strip_tags(s)
    m = re.match(r'(.+?[.!?])(\s|$)', s)
    return (m.group(1) if m else s).strip()


def T(en, he, tag='span', cls=''):
    """An English and a Hebrew twin. The site's switch shows one of them."""
    c = f' class="{cls}"' if cls else ''
    return f'<{tag}{c} data-l="en">{en}</{tag}><{tag}{c} data-l="he" dir="rtl">{he}</{tag}>'


# ---------------------------------------------------------------- shared pieces
k = SRC.find("var KEY = 'radarLang'")
SWITCH_JS = SRC[SRC.rfind('<script>', 0, k):SRC.find('</script>', k) + len('</script>')]
assert 'mail-fallback' in SWITCH_JS

MAIL_PANEL = '''
<div class="mail-fallback" id="mail-fallback" role="dialog" aria-modal="true" aria-labelledby="mail-fallback-title">
  <div class="card">
    <h3 id="mail-fallback-title" class="serif"><span data-l="en">Write to Stav</span><span data-l="he">כתבו לסתיו</span></h3>
    <p><span data-l="en">This browser has no email app set up, so nothing opened. Copy the address, or open it in your webmail.</span><span data-l="he">בדפדפן הזה לא מוגדרת תוכנת דואר, ולכן לא נפתח כלום. העתיקו את הכתובת, או פתחו אותה בדואר האינטרנטי שלכם.</span></p>
    <a class="addr" id="mail-fallback-addr" href="mailto:stav@stavtheodor.com">stav@stavtheodor.com</a>
    <div class="row">
      <button type="button" id="mail-fallback-copy"><span data-l="en">Copy</span><span data-l="he">העתקה</span></button>
      <a class="solid" id="mail-fallback-gmail" href="https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=stav@stavtheodor.com" target="_blank" rel="noopener">Gmail</a>
      <a id="mail-fallback-outlook" href="https://outlook.live.com/mail/0/deeplink/compose?to=stav@stavtheodor.com" target="_blank" rel="noopener">Outlook</a>
    </div>
    <button type="button" class="close"><span data-l="en">Close</span><span data-l="he">סגירה</span></button>
  </div>
</div>
'''

NAV = [
    ('/2/#about', 'About', 'אודות'),
    ('/2/projects/', 'Projects', 'פרויקטים'),
    ('/2/#advisory', 'Advisory', 'ייעוץ'),
    ('/2/#museum', 'Museum', 'מוזיאון'),
    ('/2/radar/', 'Art Radar', 'ראדאר אמנות'),
    ('/2/#faq', 'Questions', 'שאלות'),
    ('/2/#contact', 'Contact', 'יצירת קשר'),
]


def nav(home=False):
    links = ''.join(f'<a href="{h.replace("/2/#", "#") if home else h}">{T(en, he)}</a>' for h, en, he in NAV)
    return f'''
  <nav class="nav" aria-label="Main">
    <a class="wordmark" href="/2/">THEODORA</a>
    <div class="right">
      <div class="links" id="links">{links}</div>
      <div class="lang-switch" role="group" aria-label="Choose language / בחירת שפה">
        <button type="button" data-lang="he" aria-pressed="false">עברית</button>
        <button type="button" data-lang="en" aria-pressed="false">English</button>
      </div>
      <button type="button" class="menu-btn" id="menu-btn" aria-controls="links" aria-expanded="false">{T('Menu', 'תפריט')}</button>
    </div>
  </nav>'''


def footer():
    return f'''
<footer class="foot" id="contact">
  <div class="left">
    <p class="eyebrow">{T('Contact', 'יצירת קשר')}</p>
    <h2 class="serif">{T('Send me one photo of the wall and a line about the space. I’ll tell you what I see.', 'שלחו לי תמונה אחת של הקיר ושורה על החלל. אספר לכם מה אני רואה.')}</h2>
    <a class="arrow" href="mailto:{EMAIL}"><span class="ln"></span>{T('Write to Stav', 'כתבו לסתיו')}</a>
    <a class="arrow" href="mailto:{EMAIL}" style="text-transform: none; letter-spacing: 0.02em;"><span class="ln"></span>{EMAIL}</a>
    <div class="wordmark" style="margin-top: 40px;">THEODORA</div>
    <p style="font-size: 15px; max-width: 560px;">{T('Stav Theodor-Kimhi, art curation and advisory. Tenafly, New Jersey, for New York, New Jersey and Tel Aviv.', "סתיו תאודור-קמחי, אוצרות וייעוץ אמנות. טנפליי, ניו ג'רזי, לניו יורק, ניו ג'רזי ולתל אביב.")}</p>
  </div>
  <div class="cols2">
    <div>
      <a href="/2/#about">{T('About', 'אודות')}</a><a href="/2/projects/">{T('Projects', 'פרויקטים')}</a><a href="/2/#advisory">{T('Advisory', 'ייעוץ')}</a><a href="/museum/">{T('The Museum', 'המוזיאון')}</a><a href="/2/radar/">{T('Art Radar', 'ראדאר אמנות')}</a><a href="/2/#faq">{T('Questions', 'שאלות')}</a>
    </div>
    <div>
      <a href="{WHATSAPP}" target="_blank" rel="noopener">{T('Art Radar on WhatsApp', 'ראדאר אמנות בוואטסאפ')}</a><a href="{INSTAGRAM}" target="_blank" rel="noopener">{T('Instagram', 'אינסטגרם')}</a><a href="/2/radar/">{T('All posts', 'כל הפוסטים')}</a><a href="/">{T('Current homepage', 'דף הבית הנוכחי')}</a>
    </div>
    <p class="eyebrow copy">{T('Tenafly, New Jersey · © 2026 THEODORA', "טנפליי, ניו ג'רזי · © 2026 THEODORA")}</p>
  </div>
</footer>
'''


CSS = '''
  :root {
    --bg: #0F0F14; --surface: #1A1A20; --ink: #F2F0EC; --soft: #D8D5CF; --muted: #A5A3AC;
    --taupe: #9D7663; --taupe-ink: #1A1418; --line: rgba(242,240,236,0.14);
    --serif: 'DM Serif Display', Georgia, serif; --sans: 'Plus Jakarta Sans', Helvetica, Arial, sans-serif; --he: 'Frank Ruhl Libre', 'David Libre', serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body { background: var(--bg); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.65; -webkit-font-smoothing: antialiased; }
  [data-l="he"] { font-family: var(--he); }
  body.lang-en [data-l="he"] { display: none !important; }
  body.lang-he [data-l="en"] { display: none !important; }
  .serif { font-family: var(--serif); font-weight: 400; line-height: 1.05; letter-spacing: -0.01em; }
  .serif [data-l="he"] { font-family: var(--he); font-weight: 400; letter-spacing: 0; }
  a { color: inherit; text-decoration: none; }
  a:hover { color: #C9A46B; }
  img { display: block; max-width: 100%; }
  .eyebrow { font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color: var(--taupe); font-weight: 600; }
  .eyebrow.soft { color: var(--muted); }
  .eyebrow [data-l="he"] { letter-spacing: 0.04em; font-size: 14px; }
  .muted { color: var(--muted); }
  .body { font-size: 17px; line-height: 1.7; color: var(--soft); }
  .wrap { padding-left: clamp(20px, 3.4vw, 48px); padding-right: clamp(20px, 3.4vw, 48px); }
  .section { padding-top: clamp(88px, 10vw, 150px); }
  .head { display: flex; justify-content: space-between; align-items: flex-end; gap: 32px; flex-wrap: wrap; margin-bottom: clamp(28px, 3vw, 40px); }
  .head .lead { display: flex; flex-direction: column; gap: 16px; max-width: 900px; }
  h2.serif { font-size: clamp(30px, 3.2vw, 44px); text-wrap: balance; }
  .arrow { display: inline-flex; align-items: center; gap: 12px; font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 600; white-space: nowrap; }
  .arrow [data-l="he"] { letter-spacing: 0; text-transform: none; font-size: 16px; }
  .ln { width: 36px; height: 1px; background: currentColor; display: inline-block; flex: none; }
  .btn { display: inline-block; font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600; color: var(--ink); border: 1px solid rgba(242,240,236,0.45); padding: 16px 30px; transition: background .3s, color .3s; }
  .btn:hover { background: var(--ink); color: var(--bg); }
  .btn.big { font-size: 15px; padding: 20px 40px; border-color: var(--ink); }
  .btn [data-l="he"] { letter-spacing: 0; text-transform: none; font-size: 16px; }
  .btn.big [data-l="he"] { font-size: 18px; }
  .cover { width: 100%; height: 100%; object-fit: cover; }

  html.js .reveal { opacity: 0; transform: translateY(18px); transition: opacity .9s ease, transform .9s ease; }
  html.js .reveal.in { opacity: 1; transform: none; }
  @media (prefers-reduced-motion: reduce) { html.js .reveal { opacity: 1; transform: none; transition: none; } .hero img, .phero img { animation: none !important; } }

  .nav { position: absolute; left: 0; right: 0; top: 0; z-index: 5; display: flex; justify-content: space-between; align-items: center; padding: 26px clamp(20px, 3.4vw, 48px); }
  .nav.solid { position: relative; }
  .wordmark { font-family: var(--serif); font-size: 22px; letter-spacing: 0.22em; color: var(--ink); }
  .links { display: flex; gap: 30px; align-items: center; }
  .links a { font-size: 13px; font-weight: 500; letter-spacing: 0.02em; }
  .links a [data-l="he"] { font-size: 16px; }
  .lang-switch button { background: none; border: 0; color: var(--ink); cursor: pointer; font-family: var(--he); font-size: 16px; padding: 0; }
  .lang-switch button[data-lang="en"] { font-family: var(--sans); font-size: 13px; font-weight: 500; }
  body.lang-en .lang-switch button[data-lang="en"] { display: none; }
  body.lang-he .lang-switch button[data-lang="he"] { display: none; }
  .menu-btn { display: none; background: none; border: 0; color: var(--ink); font-family: var(--sans); font-size: 13px; font-weight: 500; cursor: pointer; }
  .menu-btn [data-l="he"] { font-size: 16px; }

  .hero { position: relative; height: 100vh; min-height: 620px; max-height: 980px; overflow: hidden; background: var(--bg); }
  .hero img { width: 100%; height: 100%; object-fit: cover; animation: drift 28s ease-in-out infinite alternate; transform-origin: 50% 50%; }
  @keyframes drift { from { transform: scale(1.04) translateY(0); } to { transform: scale(1.12) translateY(-1.5%); } }
  .hero .scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(15,15,20,0.55) 0%, rgba(15,15,20,0.12) 35%, rgba(15,15,20,0.15) 65%, rgba(15,15,20,0.85) 100%); }
  .hero .line { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 0 20px; }
  .hero h1 { font-size: clamp(44px, 7vw, 104px); text-align: center; text-shadow: 0 2px 30px rgba(0,0,0,0.35); }
  .hero .tick { position: absolute; left: 0; right: 0; bottom: 36px; display: flex; justify-content: center; }
  .hero .tick span { width: 1px; height: 56px; background: rgba(242,240,236,0.6); }

  .phero { position: relative; height: 86vh; min-height: 560px; max-height: 900px; overflow: hidden; background: var(--bg); }
  .phero img { width: 100%; height: 100%; object-fit: cover; animation: drift 28s ease-in-out infinite alternate; }
  .phero .scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(15,15,20,0.55) 0%, rgba(15,15,20,0.1) 35%, rgba(15,15,20,0.3) 65%, rgba(15,15,20,0.92) 100%); }
  .phero .title { position: absolute; left: 0; right: 0; bottom: 0; padding: 0 clamp(20px, 3.4vw, 48px) clamp(40px, 5vw, 64px); display: flex; flex-direction: column; gap: 18px; max-width: 1100px; }
  .phero h1 { font-size: clamp(38px, 5.2vw, 76px); text-wrap: balance; }
  .phero .cap { font-size: 15px; color: var(--soft); max-width: 720px; }

  .statement { display: flex; flex-direction: column; align-items: center; gap: 32px; padding: clamp(88px, 11vw, 168px) clamp(20px, 8vw, 120px) clamp(80px, 10vw, 150px); text-align: center; }
  .statement h2 { font-size: clamp(30px, 3.6vw, 52px); max-width: 1040px; }
  .plead { padding: clamp(72px, 8vw, 120px) clamp(20px, 3.4vw, 48px) 0; max-width: 1000px; }
  .plead p { font-family: var(--serif); font-size: clamp(26px, 2.6vw, 36px); line-height: 1.25; }
  .plead p [data-l="he"] { font-family: var(--he); }

  .cols { display: flex; height: 720px; }
  .col { position: relative; overflow: hidden; background: var(--surface); flex: 1; transition: flex .7s cubic-bezier(.2,.7,.2,1); }
  .col.open { flex: 1.9; }
  .col img { width: 100%; height: 100%; object-fit: cover; }
  .col .scrim { position: absolute; inset: 0; background: linear-gradient(180deg, rgba(15,15,20,0.72) 0%, rgba(15,15,20,0.08) 45%, rgba(15,15,20,0.55) 100%); }
  .col .text { position: absolute; left: 32px; right: 32px; top: 36px; display: flex; flex-direction: column; gap: 18px; max-width: 460px; }
  .col h3 { font-size: 26px; }
  .col.open h3 { font-size: 34px; }
  .col .desc { font-size: 15px; line-height: 1.65; color: #E6E3DE; opacity: 0; transition: opacity .5s .2s; }
  .col.open .desc { opacity: 1; }

  .about { display: grid; grid-template-columns: minmax(0, 520px) minmax(0, 1fr); gap: clamp(32px, 6vw, 96px); align-items: center; }
  .about .portrait { overflow: hidden; background: var(--surface); }
  .about .portrait img { width: 100%; height: auto; filter: grayscale(100%); }
  .about .text { display: flex; flex-direction: column; gap: 22px; max-width: 680px; }
  .role { font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
  .role [data-l="he"] { letter-spacing: 0; text-transform: none; font-size: 15px; }

  .film video { display: block; width: 100%; aspect-ratio: 16 / 9; background: var(--surface); }
  .film .cap { margin-top: 18px; font-size: 15px; color: var(--muted); }

  .grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 40px 24px; }
  .card { display: flex; flex-direction: column; gap: 14px; }
  .card .ph { height: 320px; overflow: hidden; background: var(--surface); }
  .card .ph img { width: 100%; height: 100%; object-fit: cover; transition: transform 1.2s ease; }
  .card:hover .ph img { transform: scale(1.04); }
  .card h3 { font-size: 24px; }
  .card p { font-size: 14px; }

  .rows { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 64px; border-bottom: 1px solid var(--line); }
  .row { display: grid; grid-template-columns: minmax(0, 1fr) 40px; gap: 24px; align-items: center; padding: 26px 0; border-top: 1px solid var(--line); }
  .row h3 { font-size: 24px; }

  .museum { position: relative; min-height: 640px; overflow: hidden; background: var(--surface); margin-top: clamp(88px, 10vw, 150px); display: flex; align-items: center; }
  .museum img.bg { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 30%; }
  .museum .scrim { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(15,15,20,0.94) 0%, rgba(15,15,20,0.8) 45%, rgba(15,15,20,0.4) 100%); }
  .museum .text { position: relative; display: flex; flex-direction: column; gap: 24px; max-width: 640px; padding: 88px clamp(20px, 3.4vw, 48px); }
  .museum h2 { font-size: clamp(32px, 3.4vw, 48px); }

  .radar-intro { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: clamp(32px, 6vw, 96px); align-items: start; }
  .radar-intro .left { display: flex; flex-direction: column; gap: 22px; }
  .radar-intro .right { display: flex; flex-direction: column; gap: 18px; padding-top: 44px; }

  /* the posts timeline */
  .timeline { position: relative; margin-top: clamp(40px, 5vw, 64px); padding-left: 44px; }
  .timeline::before { content: ""; position: absolute; left: 6px; top: 0; bottom: 0; width: 1px; background: linear-gradient(180deg, var(--taupe) 0%, rgba(157,118,99,0.35) 100%); }
  .month { position: relative; padding: 8px 0 8px 0; margin-top: 40px; }
  .month:first-child { margin-top: 0; }
  .month::before { content: ""; position: absolute; left: -44px; top: 12px; width: 13px; height: 13px; background: var(--bg); border: 1px solid var(--taupe); }
  .entry { position: relative; display: grid; grid-template-columns: 170px minmax(0, 1fr) 220px; gap: 32px; align-items: center; padding: 26px 0; border-top: 1px solid var(--line); }
  .entry::before { content: ""; position: absolute; left: -41px; top: 50%; width: 7px; height: 7px; margin-top: -3px; background: var(--taupe); }
  .entry .date { font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
  .entry .date [data-l="he"] { letter-spacing: 0; text-transform: none; font-size: 15px; }
  .entry h3 { font-size: 26px; }
  .entry .teaser { font-size: 14px; color: var(--muted); margin-top: 8px; }
  .entry .th { height: 132px; overflow: hidden; background: var(--surface); }
  .entry .th img { width: 100%; height: 100%; object-fit: cover; transition: transform 1.2s ease; }
  .entry:hover .th img { transform: scale(1.04); }
  .entry:hover h3 { color: #C9A46B; }
  .cta-posts { display: flex; flex-direction: column; align-items: center; gap: 28px; text-align: center; padding: clamp(64px, 7vw, 96px) 20px 0; }
  .cta-posts h2 { font-size: clamp(30px, 3.4vw, 48px); }

  .qas { display: flex; flex-direction: column; border-bottom: 1px solid var(--line); max-width: 1040px; }
  .qa { border-top: 1px solid var(--line); }
  .qa summary { list-style: none; cursor: pointer; display: grid; grid-template-columns: minmax(0, 1fr) 40px; gap: 24px; align-items: center; padding: 26px 0; }
  .qa summary::-webkit-details-marker { display: none; }
  .qa h3 { font-size: 26px; }
  .qa .plus { width: 40px; height: 40px; border: 1px solid rgba(242,240,236,0.3); position: relative; }
  .qa .plus::before, .qa .plus::after { content: ""; position: absolute; left: 50%; top: 50%; background: var(--ink); transform: translate(-50%, -50%); width: 14px; height: 1px; }
  .qa .plus::after { width: 1px; height: 14px; transition: transform .3s; }
  .qa[open] .plus::after { transform: translate(-50%, -50%) scaleY(0); }
  .qa .body { max-width: 820px; padding: 0 0 30px; }

  /* project page prose */
  .prose { max-width: 860px; }
  .prose h2 { font-family: var(--serif); font-weight: 400; font-size: clamp(26px, 2.4vw, 32px); line-height: 1.1; margin: 52px 0 18px; letter-spacing: -0.01em; }
  .prose[data-l="he"] h2 { font-family: var(--he); }
  .prose p { font-size: 18px; line-height: 1.75; color: var(--soft); margin: 0 0 22px; }
  .prose ul, .prose ol { margin: 0 0 22px 22px; color: var(--soft); font-size: 18px; line-height: 1.75; }
  .prose[data-l="he"] ul, .prose[data-l="he"] ol { margin: 0 22px 22px 0; }
  .prose a { border-bottom: 1px solid rgba(242,240,236,0.35); }
  .prose strong { color: var(--ink); font-weight: 600; }
  .prose blockquote { border-left: 1px solid var(--taupe); padding-left: 24px; margin: 36px 0; font-family: var(--serif); font-size: 26px; line-height: 1.3; color: var(--ink); }
  .prose[data-l="he"] blockquote { border-left: 0; border-right: 1px solid var(--taupe); padding-left: 0; padding-right: 24px; font-family: var(--he); }
  .prose figure { margin: 44px 0; }
  .prose figure img { width: 100%; height: auto; }
  .prose figcaption { font-size: 14px; color: var(--muted); margin-top: 12px; }
  .next { display: flex; flex-direction: column; gap: 18px; padding-top: clamp(88px, 10vw, 150px); }
  .next a.big { font-family: var(--serif); font-size: clamp(34px, 4.4vw, 64px); line-height: 1.05; letter-spacing: -0.01em; text-wrap: balance; }
  .next a.big [data-l="he"] { font-family: var(--he); }
  .readnext { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
  .readnext a { font-size: 16px; color: var(--soft); border-bottom: 1px solid var(--line); align-self: flex-start; }

  .foot { background: var(--taupe); color: var(--taupe-ink); margin-top: clamp(88px, 10vw, 150px); padding: clamp(64px, 7vw, 96px) clamp(20px, 3.4vw, 48px) 48px; display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: clamp(40px, 6vw, 80px); }
  .foot a { color: var(--taupe-ink); }
  .foot a:hover { color: var(--ink); }
  .foot .eyebrow { color: #3D2E27; }
  .foot .left { display: flex; flex-direction: column; gap: 26px; }
  .foot h2 { font-size: clamp(30px, 3.2vw, 44px); line-height: 1.15; max-width: 680px; }
  .foot .cols2 { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; align-content: start; padding-top: 6px; }
  .foot .cols2 > div { display: flex; flex-direction: column; gap: 12px; font-size: 14px; font-weight: 500; }
  .foot .cols2 [data-l="he"] { font-size: 16px; }
  .foot .copy { grid-column: 1 / -1; margin-top: 40px; }

  .mail-fallback { position: fixed; inset: 0; background: rgba(15,15,20,0.72); display: none; align-items: center; justify-content: center; padding: 24px; z-index: 9999; }
  .mail-fallback.open { display: flex; }
  .mail-fallback .card { background: var(--surface); border: 1px solid var(--line); max-width: 420px; width: 100%; padding: 30px 30px 26px; text-align: center; display: block; }
  .mail-fallback h3 { font-size: 26px; margin-bottom: 8px; }
  .mail-fallback p { font-size: 15px; color: var(--muted); margin-bottom: 18px; }
  .mail-fallback .addr { display: block; font-size: 18px; color: var(--ink); border: 1px solid var(--line); padding: 12px 14px; margin-bottom: 16px; word-break: break-all; direction: ltr; }
  .mail-fallback .row { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; border: 0; padding: 0; grid-template-columns: none; }
  .mail-fallback .row a, .mail-fallback .row button { font-family: var(--sans); font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; padding: 10px 16px; border: 1px solid var(--taupe); background: transparent; color: var(--ink); cursor: pointer; }
  .mail-fallback .row a.solid { background: var(--taupe); color: var(--taupe-ink); }
  .mail-fallback .close { margin-top: 16px; background: none; border: 0; font-family: var(--sans); font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); cursor: pointer; }

  @media (max-width: 900px) {
    .links { display: none; position: fixed; inset: 0; background: var(--bg); flex-direction: column; justify-content: center; align-items: center; gap: 28px; z-index: 20; }
    .links a { font-family: var(--serif); font-size: 32px; letter-spacing: 0; }
    .links a [data-l="he"] { font-size: 30px; }
    body.menu-open .links { display: flex; }
    .menu-btn { display: inline-block; position: relative; z-index: 30; }
    .nav .lang-switch { position: relative; z-index: 30; }
    .nav .right { display: flex; gap: 18px; align-items: center; }
    .hero { height: 78vh; min-height: 560px; }
    .phero { height: 72vh; min-height: 520px; }
    .cols { flex-direction: column; height: auto; }
    .col, .col.open { flex: none; height: 260px; }
    .col:first-child { height: 320px; }
    .col .text { left: 20px; right: 20px; top: auto; bottom: 20px; }
    .col .scrim { background: linear-gradient(180deg, rgba(15,15,20,0.15) 0%, rgba(15,15,20,0.78) 100%); }
    .col h3, .col.open h3 { font-size: 24px; }
    .col .desc { opacity: 1; font-size: 14px; }
    .about { grid-template-columns: 1fr; }
    .about .portrait { max-width: 260px; }
    .grid3 { grid-template-columns: 1fr; gap: 32px; }
    .card .ph { height: 240px; }
    .rows { grid-template-columns: 1fr; }
    .row h3, .qa h3 { font-size: 20px; }
    .museum { min-height: 0; }
    .museum .scrim { background: linear-gradient(180deg, rgba(15,15,20,0.55) 0%, rgba(15,15,20,0.92) 100%); }
    .museum .text { padding: 64px 20px; }
    .radar-intro { grid-template-columns: 1fr; }
    .radar-intro .right { padding-top: 0; }
    .timeline { padding-left: 28px; }
    .month::before { left: -28px; }
    .entry { grid-template-columns: 1fr; gap: 12px; }
    .entry::before { left: -25px; top: 40px; }
    .entry .th { height: 200px; order: -1; }
    .entry h3 { font-size: 22px; }
    .foot { grid-template-columns: 1fr; }
    .btn { display: block; text-align: center; }
  }
  @media (min-width: 901px) { .nav .right { display: flex; gap: 30px; align-items: center; } }
'''

BOOT_JS = '''
<script>
(function () {
  document.documentElement.classList.add('js');
  var def = document.documentElement.getAttribute('data-default-lang') || 'en';
  var lang = def;
  try { lang = localStorage.getItem('radarLang') || def; } catch (e) {}
  if (lang !== 'he' && lang !== 'en') { lang = def; }
  document.body.classList.toggle('lang-en', lang === 'en');
  document.body.classList.toggle('lang-he', lang === 'he');
  document.documentElement.lang = lang;
})();
</script>'''

PAGE_JS = '''
<script>
(function () {
  var btn = document.getElementById('menu-btn');
  if (btn) {
    btn.addEventListener('click', function () {
      var open = document.body.classList.toggle('menu-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.querySelectorAll('#links a').forEach(function (a) { a.addEventListener('click', function () { document.body.classList.remove('menu-open'); btn.setAttribute('aria-expanded', 'false'); }); });
  }
  var cols = document.querySelectorAll('.cols .col');
  cols.forEach(function (c) {
    c.addEventListener('mouseenter', function () { cols.forEach(function (o) { o.classList.toggle('open', o === c); }); });
    c.addEventListener('focusin', function () { cols.forEach(function (o) { o.classList.toggle('open', o === c); }); });
  });
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
  }
})();
</script>'''


def head(title, desc, og_image='/og-image.jpg'):
    return f'''<!DOCTYPE html>
<html lang="en" data-default-lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{H.escape(title)}</title>
<meta name="robots" content="noindex">
<meta name="description" content="{H.escape(desc, quote=True)}">
<meta property="og:title" content="{H.escape(title, quote=True)}">
<meta property="og:description" content="{H.escape(desc, quote=True)}">
<meta property="og:image" content="https://stavtheodor.com{og_image}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Plus+Jakarta+Sans:wght@400;500;600&family=Frank+Ruhl+Libre:wght@300;400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
</head>
<body class="lang-en">{BOOT_JS}
'''


def tail():
    return f'{footer()}{MAIL_PANEL}{SWITCH_JS}{PAGE_JS}\n</body>\n</html>\n'


# ---------------------------------------------------------------- content
KICKER_HE = {
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
PROJECT_ORDER = [
    'caesarea-garden-villa', 'caesarea-sea-view-villa-triptych', 'closter-new-jersey-new-construction',
    'herzliya-pituach-sea-view-apartment', 'hod-hasharon-private-villa', 'ramat-gan-private-home',
    'caesarea-private-estate', 'caesarea-luxury-residence-home-office', 'manhattan-skyline-residence',
    'tel-aviv-bauhaus-residence', 'tel-aviv-home-of-roni-daloomi', 'tel-aviv-private-residence-shtisel-commission',
    'tel-aviv-renovated-bauhaus-home', 'hotels-and-hospitality-collections', 'creating-hope-exhibition-un-geneva',
]


def load_projects():
    pages = {}
    for f in glob.glob(os.path.join(ROOT, 'content', 'pages', '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('section') == 'projects':
            pages[d['path'].split('/')[-1]] = d
    missing = [s for s in PROJECT_ORDER if s not in pages]
    assert not missing, missing
    extra = [s for s in pages if s not in PROJECT_ORDER]
    return [pages[s] | {'slug': s} for s in PROJECT_ORDER + sorted(extra)]


def load_posts():
    posts = []
    for m in re.finditer(r'<article class="post" id="([^"]+)">(.*?)</article>', SRC, flags=re.S):
        slug, body = m.group(1), m.group(2)
        if not os.path.isdir(os.path.join(ROOT, 'radar', slug)):
            continue  # the template article, or a post without a permalink yet
        def grab(rx):
            mm = re.search(rx, body, flags=re.S)
            return strip_tags(mm.group(1)) if mm else ''
        date_en = grab(r'<div class="post-date" data-l="en">(.*?)</div>')
        date_he = grab(r'<div class="post-date" data-l="he"[^>]*>(.*?)</div>')
        title_en = title_he = ''
        for attrs, inner in re.findall(r'<h2 class="post-title[^"]*"([^>]*)>(.*?)</h2>', body, flags=re.S):
            tag = attrs + ' '
            if 'post-title-he' in tag or 'data-l="he"' in tag or 'dir="rtl"' in tag:
                title_he = title_he or strip_tags(inner)
            else:
                title_en = title_en or strip_tags(inner)
        # the newer markup carries the language in the class name
        m_en = re.search(r'<h2 class="post-title post-title-en"[^>]*>(.*?)</h2>', body, flags=re.S)
        m_he = re.search(r'<h2 class="post-title post-title-he"[^>]*>(.*?)</h2>', body, flags=re.S)
        if m_en: title_en = strip_tags(m_en.group(1))
        if m_he: title_he = strip_tags(m_he.group(1))
        en_body = re.search(r'<div class="post-body post-body-en"[^>]*>(.*?)$', body, flags=re.S)
        he_body = re.search(r'<div class="post-body" lang="he"[^>]*>(.*?)<div class="post-body post-body-en"', body, flags=re.S)
        p_en = re.search(r'<p[^>]*>(.*?)</p>', en_body.group(1), flags=re.S) if en_body else None
        p_he = re.search(r'<p[^>]*>(.*?)</p>', he_body.group(1), flags=re.S) if he_body else None
        img = re.search(r'<img[^>]+src="([^"]+)"', body)
        src = img.group(1) if img else ''
        if src and not src.startswith('/'):
            src = '/' + src
        assert date_en and title_en and title_he, slug
        posts.append(dict(slug=slug, date_en=date_en, date_he=date_he, title_en=title_en, title_he=title_he,
                          teaser_en=first_sentence(p_en.group(1)) if p_en else '', teaser_he=first_sentence(p_he.group(1)) if p_he else '', img=src))
    assert len(posts) >= 20, len(posts)
    return posts


def month_labels(post):
    m = re.match(r'([A-Za-z]+) \d+, (\d{4})', post['date_en'])
    en = f'{m.group(1)} {m.group(2)}' if m else post['date_en']
    mh = re.match(r'\d+ ב(.+)$', post['date_he'])
    he = mh.group(1) if mh else post['date_he']
    return en, he


def timeline(posts, with_months):
    out = []
    last = None
    for p in posts:
        mon = month_labels(p)
        if with_months and mon != last:
            out.append(f'<div class="month"><p class="eyebrow">{T(mon[0], mon[1])}</p></div>')
            last = mon
        th = f'<div class="th"><img src="{p["img"]}" alt="" loading="lazy"></div>' if p['img'] else '<div class="th"></div>'
        teaser = f'<p class="teaser">{T(H.escape(p["teaser_en"]), H.escape(p["teaser_he"]))}</p>' if p['teaser_en'] else ''
        out.append(f'''
      <a class="entry reveal" href="/radar/{p['slug']}/">
        <div class="date">{T(p['date_en'], p['date_he'])}</div>
        <div><h3 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h3>{teaser}</div>
        {th}
      </a>''')
    return ''.join(out)


def project_card(p):
    return f'''
      <a class="card reveal" href="/2/projects/{p['slug']}/">
        <div class="ph"><img src="{p['hero_image']['src']}" alt="{H.escape(p['hero_image'].get('alt_en', ''), quote=True)}" loading="lazy"></div>
        <h3 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h3>
        <p class="muted">{T(H.escape(first_sentence(p['lead_en'])), H.escape(first_sentence(p['lead_he'])))}</p>
      </a>'''


# ---------------------------------------------------------------- pages
def render_home(projects, posts):
    cols_data = [
        ('col-curation.jpg', 'Art Consulting &amp; Curation', 'ייעוץ ואוצרות אמנות', 'From a single artwork to a complete collection', 'מיצירה אחת ועד אוסף שלם', 'Stav Theodor holding a framed work in a gallery corridor lined with paintings'),
        ('col-sourcing.jpg', 'Sourcing &amp; Acquisition', 'איתור ורכישה', 'Personalized, through a global network of artists and makers', 'בהתאמה אישית, דרך רשת גלובלית של אמנים ויוצרים', 'A tall blue portrait in a slim black frame on a lit wall'),
        ('col-commissions.jpg', 'Commissions &amp; Creative Direction', 'הזמנות עבודה וניהול קריאייטיב', 'From first concept to final execution', 'מהקונספט הראשון ועד הביצוע הסופי', 'The three panel stork triptych installed on a white wall'),
        ('col-production.jpg', 'Production &amp; Installation', 'הפקה והתקנה', 'Framing and placement, managed end to end', 'מסגור והצבה, בניהול מלא מקצה לקצה', 'Stav Theodor at a print studio table, unwrapping a canvas'),
    ]
    cols = ''.join(f'''
      <div class="col{' open' if i == 0 else ''}">
        <img src="/images/home2/{img}" alt="{alt}" loading="lazy">
        <div class="scrim"></div>
        <div class="text"><h3 class="serif">{T(en, he)}</h3><p class="desc">{T(den, dhe)}</p></div>
      </div>''' for i, (img, en, he, den, dhe, alt) in enumerate(cols_data))
    advisory = [
        ('/advisory/', 'Art advisory, answered plainly: what it costs, how it works, where I work', 'ייעוץ אמנות בשפה פשוטה: כמה זה עולה, איך זה עובד, ואיפה אני עובדת'),
        ('/2/projects/', 'Projects: homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels, one exhibition in Geneva', "פרויקטים: בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות, ותערוכה אחת בז'נבה"),
        ('/for-designers/', 'For interior designers and architects', 'למעצבי פנים ולאדריכלים'),
        ('/for-brokers/', 'For real estate brokers and developers: art for the new home', 'למתווכי נדל"ן וליזמים: אמנות לבית החדש'),
        ('/for-advisors/', 'For wealth managers, family offices and private bankers', 'למנהלי הון, למשרדי משפחה ולבנקאים פרטיים'),
        ('/guide/ten-questions-before-you-buy-your-first-serious-artwork/', 'Ten questions to answer before you buy your first serious artwork', 'עשר שאלות שכדאי לענות עליהן לפני רכישת היצירה הרצינית הראשונה'),
    ]
    rows = ''.join(f'<a class="row" href="{h}"><h3 class="serif">{T(en, he)}</h3><span class="ln"></span></a>' for h, en, he in advisory)
    faq_en = re.findall(r'<div class="faq-item" data-l="en"[^>]*>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>', SRC, flags=re.S)
    faq_he = re.findall(r'<div class="faq-item" data-l="he"[^>]*>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>', SRC, flags=re.S)
    assert len(faq_en) == len(faq_he) == 7
    faq = ''.join(f'''
      <details class="qa"{' open' if i == 0 else ''}>
        <summary><h3 class="serif">{T(qe.strip(), qh.strip())}</h3><span class="plus" aria-hidden="true"></span></summary>
        <p class="body">{T(ae.strip(), ah.strip())}</p>
      </details>''' for i, ((qe, ae), (qh, ah)) in enumerate(zip(faq_en, faq_he)))
    n = len(posts)
    return head('Art Advisor & Curator, NYC · NJ · Tel Aviv | THEODORA', 'Art Advisor & Curator for private clients and businesses in NYC, NJ & Tel Aviv. Discover, select, and acquire exceptional art with expert guidance.') + f'''
<header class="hero">
  <img src="/images/home2/hero-caesarea.jpg" alt="A large painting of a rider on a blue horse with gold detailing, hung on a stone wall between two brass sconces" fetchpriority="high">
  <div class="scrim"></div>{nav(home=True)}
  <div class="line"><h1 class="serif">{T('Art is not an accessory.', 'אמנות היא לא אקססורי.')}</h1></div>
  <div class="tick"><span></span></div>
</header>

<section class="statement">
  <p class="eyebrow reveal">{T('What I do', 'מה אני עושה')}</p>
  <h2 class="serif reveal">{T("I don’t simply place art in spaces, I connect people with the art they are meant to live with.", 'אני לא רק מציבה אמנות בחללים, אני מחברת בין אנשים לאמנות שנועדה לחיות איתם.')}</h2>
</section>

<section class="cols" id="services" aria-label="Services">{cols}
</section>

<section class="section wrap" id="about">
  <div class="about">
    <div class="portrait reveal"><img src="/images/stav-portrait.jpg" alt="Stav Theodor-Kimhi" loading="lazy"></div>
    <div class="text reveal">
      <p class="eyebrow">{T('About', 'אודות')}</p>
      <h2 class="serif">{T('Stav Theodor&#8209;Kimhi', 'סתיו תאודור&#8209;קמחי')}</h2>
      <p class="role">{T('Founder &amp; Art Curator', 'מייסדת ואוצרת אמנות')}</p>
      <p class="body">{T('I founded THEODORA after two decades across the art world: museums, galleries, academia, and years of work alongside leaders in international hospitality, building art concepts and collections for projects from hotels to private homes. That experience taught me one thing above all: the right piece, in the right space, at the right moment, changes how a person sees.', 'הקמתי את THEODORA אחרי שני עשורים בעולם האמנות: מוזיאונים, גלריות, אקדמיה, ושנים של עבודה לצד מובילים בתחום האירוח הבינלאומי, בבניית קונספטים ואוספים של אמנות לפרויקטים ממלונות ועד בתים פרטיים. הניסיון הזה לימד אותי דבר אחד מעל הכול: היצירה הנכונה, בחלל הנכון, ברגע הנכון, משנה את האופן שבו אדם רואה.')}</p>
      <p class="body">{T('THEODORA exists to help people discover that connection. To find artworks that resonate on a personal level and create spaces that feel meaningful, distinctive, and alive. Recent projects include private residences in Caesarea, Tel Aviv, and Herzliya, large-scale hospitality commissions, and the exhibition Creating Hope.', 'THEODORA קיימת כדי לעזור לאנשים לגלות את החיבור הזה. למצוא יצירות שמהדהדות ברמה האישית, וליצור חללים שמרגישים משמעותיים, ייחודיים וחיים. בין הפרויקטים האחרונים: בתים פרטיים בקיסריה, בתל אביב ובהרצליה, הזמנות בקנה מידה גדול לעולם האירוח, והתערוכה Creating Hope.')}</p>
    </div>
  </div>
</section>

<section class="section wrap film" id="film">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('The film', 'הסרט')}</p><h2 class="serif">{T('Seventy five seconds on what I do.', 'שבעים וחמש שניות על מה שאני עושה.')}</h2></div></div>
  <video controls playsinline preload="metadata" poster="/images/home2/film-still.jpg" class="reveal">
    <source src="/videos/theodora-film-2026-09.mp4" type="video/mp4">
  </video>
  <p class="cap">{T('Seventy five seconds on what I do, for designers, private collectors, home and business owners.', 'שבעים וחמש שניות על מה שאני עושה, למעצבים, לאספנים פרטיים, לבעלי בתים ולבעלי עסקים.')}</p>
</section>

<section class="section wrap" id="projects">
  <div class="head reveal">
    <div class="lead"><p class="eyebrow">{T('Projects', 'פרויקטים')}</p><h2 class="serif">{T('Hotels by the sea, private homes, commissioned works, and the artists behind them.', 'מלונות מול הים, בתים פרטיים, עבודות מוזמנות והאמנים שמאחוריהן.')}</h2><p class="muted" style="font-size: 17px;">{T('The best introduction to what I do is to see it.', 'הדרך הטובה ביותר להכיר את מה שאני עושה היא פשוט לראות.')}</p></div>
    <a class="arrow" href="/2/projects/"><span class="ln"></span>{T('All projects', 'כל הפרויקטים')}</a>
  </div>
  <div class="grid3">{''.join(project_card(p) for p in projects[:6])}
  </div>
</section>

<section class="section wrap" id="advisory">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('Advisory', 'ייעוץ')}</p><h2 class="serif">{T('If you are about to buy, build or move, start here.', 'אם אתם עומדים לקנות, לבנות או לעבור דירה, התחילו כאן.')}</h2><p class="muted" style="font-size: 17px; max-width: 760px;">{T('These pages answer the questions I am asked most, in plain terms, and show the work behind the answers.', 'העמודים האלה עונים בשפה פשוטה על השאלות שאני נשאלת הכי הרבה, ומראים את העבודה שמאחורי התשובות.')}</p></div></div>
  <div class="rows reveal">{rows}</div>
</section>

<section class="museum" id="museum">
  <img class="bg" src="/images/home2/museum-timeline.jpg" alt="" loading="lazy">
  <div class="scrim"></div>
  <div class="text reveal">
    <p class="eyebrow">{T('The Museum', 'המוזיאון')}</p>
    <h2 class="serif">{T('A walkable map of art history', 'מפה של תולדות האמנות שאפשר לטייל בה')}</h2>
    <p class="body">{T('An interactive museum of art history. Zoom through 40,000 years, from the painted caves through Egypt, Greece, and Rome to today, on a living timeline. Open a placard, and step inside a walkable 3D gallery hung with real artworks. Every fact and image comes from Wikipedia and Wikimedia Commons.', 'מוזיאון אינטראקטיבי של תולדות האמנות. שוטטו לאורך 40,000 שנה, מהמערות המצוירות דרך מצרים, יוון ורומא ועד ימינו, על ציר זמן חי. פתחו שלט הסבר, והיכנסו לגלריה תלת ממדית שאפשר להסתובב בתוכה, ובה יצירות אמיתיות על הקירות. כל עובדה וכל תמונה מגיעות מוויקיפדיה ומוויקישיתוף.')}</p>
    <a class="btn" href="/museum/" style="align-self: flex-start;">{T('Enter the Museum', 'כניסה למוזיאון')}</a>
  </div>
</section>

<section class="section wrap" id="radar">
  <div class="radar-intro reveal">
    <div class="left">
      <p class="eyebrow">{T('Art Radar', 'ראדאר אמנות')}</p>
      <h2 class="serif">{T('The art worth seeing, chosen by a curator.', 'האמנות ששווה לראות, בבחירת אוצרת.')}</h2>
      <a class="btn" href="{WHATSAPP}" target="_blank" rel="noopener" style="align-self: flex-start; margin-top: 10px;">{T('Join the WhatsApp Group', 'הצטרפו לקבוצת הוואטסאפ')}</a>
    </div>
    <div class="right">
      <p class="body">{T('Art Radar began as a WhatsApp group for our community in northern New Jersey and New York: a weekly radar of the exhibitions, gallery openings, public installations, art fairs, and museum events that are truly worth your time. Some weeks it is a long list. Some weeks it is one precise recommendation.', "ראדאר אמנות התחיל כקבוצת וואטסאפ לקהילה שלנו בצפון ניו ג'רזי ובניו יורק: ראדאר שבועי של התערוכות, פתיחות הגלריות, המיצבים הציבוריים, ירידי האמנות ואירועי המוזיאונים ששווים באמת את הזמן שלכם. יש שבועות שזו רשימה ארוכה. יש שבועות שזו המלצה אחת מדויקת.")}</p>
      <p class="body">{T('The posts are written in Hebrew and published in the group first. They are collected here in order, each with a full English translation, so you can always come back to them.', 'הפוסטים נכתבים בעברית ומתפרסמים קודם כול בקבוצה. הם נאספים כאן לפי הסדר, כל אחד עם תרגום מלא לאנגלית, כדי שתמיד אפשר יהיה לחזור אליהם.')}</p>
    </div>
  </div>
  <div class="timeline" id="posts">{timeline(posts[:6], with_months=False)}
  </div>
  <div class="cta-posts reveal">
    <h2 class="serif">{T(f'All {n} posts, in order, since the first radar.', f'כל {n} הפוסטים, לפי הסדר, מהראדאר הראשון ועד היום.')}</h2>
    <a class="btn big" href="/2/radar/">{T('See all posts', 'לכל הפוסטים')}</a>
  </div>
</section>

<section class="section wrap" id="faq">
  <div class="head reveal" style="justify-content: center; text-align: center;"><div class="lead" style="align-items: center;"><p class="eyebrow">{T('Questions', 'שאלות')}</p><h2 class="serif">{T('What people ask before they write.', 'מה שואלים לפני שכותבים.')}</h2></div></div>
  <div class="qas reveal" style="margin: 0 auto;">{faq}
  </div>
</section>
''' + tail()


def render_project(p, projects):
    i = projects.index(p)
    nxt = projects[(i + 1) % len(projects)]
    more = [projects[(i + j) % len(projects)] for j in (1, 2, 3)]
    kicker_he = KICKER_HE.get(p.get('kicker', ''), p.get('kicker', ''))
    hero = p['hero_image']
    faq = ''
    if p.get('faq'):
        faq = '<section class="section wrap"><div class="head"><div class="lead"><p class="eyebrow">' + T('Questions', 'שאלות') + '</p></div></div><div class="qas">' + ''.join(
            f'<details class="qa"><summary><h3 class="serif">{T(q["q_en"], q["q_he"])}</h3><span class="plus" aria-hidden="true"></span></summary><p class="body">{T(q["a_en"], q["a_he"])}</p></details>' for q in p['faq']) + '</div></section>'
    readnext = [r for r in p.get('related', []) if not r.startswith('projects/')]
    read_html = ''
    if readnext:
        links = []
        for r in readnext:
            f = os.path.join(ROOT, 'content', 'pages', r.split('/')[-1] + '.json')
            if os.path.exists(f):
                d = json.load(open(f, encoding='utf-8'))
                links.append(f'<a href="/{r.strip("/")}/">{T(H.escape(d["title_en"]), H.escape(d["title_he"]))}</a>')
        if links:
            read_html = f'<div class="readnext"><p class="eyebrow soft" style="margin-top: 24px;">{T("Read next", "להמשך קריאה")}</p>{"".join(links)}</div>'
    return head(f"{p['title_en']} · THEODORA", p.get('meta_description') or first_sentence(p['lead_en']), hero['src']) + f'''
<header class="phero">
  <img src="{hero['src']}" alt="{H.escape(hero.get('alt_en', ''), quote=True)}" fetchpriority="high">
  <div class="scrim"></div>{nav()}
  <div class="title">
    <p class="eyebrow">{T('Projects · ' + H.escape(p.get('kicker', '')), 'פרויקטים · ' + kicker_he)}</p>
    <h1 class="serif">{T(H.escape(p['title_en']), H.escape(p['title_he']))}</h1>
    <p class="cap">{T(H.escape(hero.get('caption_en', '')), H.escape(hero.get('caption_he', '')))}</p>
  </div>
</header>

<section class="plead"><p class="reveal">{T(H.escape(p['lead_en']), H.escape(p['lead_he']))}</p></section>

<section class="section wrap">
  <div class="prose" data-l="en">{p['body_en']}</div>
  <div class="prose" data-l="he" dir="rtl">{p['body_he']}</div>
</section>
{faq}
<section class="section wrap">
  <div class="head reveal"><div class="lead"><p class="eyebrow">{T('More projects', 'עוד פרויקטים')}</p></div><a class="arrow" href="/2/projects/"><span class="ln"></span>{T('All projects', 'כל הפרויקטים')}</a></div>
  <div class="grid3">{''.join(project_card(q) for q in more)}
  </div>
  <div class="next reveal">
    <p class="eyebrow">{T('Next project', 'הפרויקט הבא')}</p>
    <a class="big" href="/2/projects/{nxt['slug']}/">{T(H.escape(nxt['title_en']), H.escape(nxt['title_he']))}</a>
    {read_html}
  </div>
</section>
''' + tail()


def render_projects_index(projects):
    return head('Projects · THEODORA', 'Homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels, and one exhibition that reached Geneva. What each space asked for and what answered it.') + f'''
<header class="phero" style="height: 62vh; min-height: 480px;">
  <img src="/images/home2/garden-villa.jpg" alt="Foyer of a Caesarea garden villa, two tall portraits facing the front door" fetchpriority="high">
  <div class="scrim"></div>{nav()}
  <div class="title">
    <p class="eyebrow">{T('Projects', 'פרויקטים')}</p>
    <h1 class="serif">{T('Homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels from Chengdu to Amman, and one exhibition that reached Geneva.', "בתים במנהטן, בניו ג'רזי, בתל אביב ובקיסריה, מלונות מצ'נגדו ועד עמאן, ותערוכה אחת שהגיעה לז'נבה.")}</h1>
    <p class="cap">{T('Each page tells what the space asked for and what answered it.', 'כל עמוד מספר מה החלל ביקש ומה ענה לו.')}</p>
  </div>
</header>

<section class="section wrap">
  <div class="grid3">{''.join(project_card(p) for p in projects)}
  </div>
</section>
''' + tail()


def render_radar_index(posts):
    n = len(posts)
    return head('Art Radar · every post · THEODORA', 'Every Art Radar post in order: exhibitions, openings and museum events in New York, New Jersey and Tel Aviv, chosen by curator Stav Theodor-Kimhi.') + f'''
<header class="phero" style="height: 62vh; min-height: 480px;">
  <img src="{posts[0]['img'] or '/images/home2/hero-caesarea.jpg'}" alt="" fetchpriority="high">
  <div class="scrim"></div>{nav()}
  <div class="title">
    <p class="eyebrow">{T('Art Radar', 'ראדאר אמנות')}</p>
    <h1 class="serif">{T(f'Every post, in order. {n} so far.', f'כל הפוסטים, לפי הסדר. {n} עד היום.')}</h1>
    <p class="cap">{T('The art worth seeing in New York, New Jersey and Tel Aviv, chosen by a curator. Written in Hebrew first, each with a full English translation.', "האמנות ששווה לראות בניו יורק, בניו ג'רזי ובתל אביב, בבחירת אוצרת. נכתב קודם בעברית, וכל פוסט עם תרגום מלא לאנגלית.")}</p>
  </div>
</header>

<section class="section wrap" style="padding-top: clamp(56px, 6vw, 88px);">
  <div class="head reveal">
    <div class="lead"><p class="eyebrow">{T('Get it first', 'קבלו את זה ראשונים')}</p><h2 class="serif">{T('The posts go to the WhatsApp group first.', 'הפוסטים מגיעים קודם לקבוצת הוואטסאפ.')}</h2></div>
    <a class="btn" href="{WHATSAPP}" target="_blank" rel="noopener">{T('Join the WhatsApp Group', 'הצטרפו לקבוצת הוואטסאפ')}</a>
  </div>
  <div class="timeline">{timeline(posts, with_months=True)}
  </div>
</section>
''' + tail()


# ---------------------------------------------------------------- write
def write(path, html_text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(html_text)
    return full


def main():
    projects = load_projects()
    posts = load_posts()
    written = [write('2/index.html', render_home(projects, posts)),
               write('2/projects/index.html', render_projects_index(projects)),
               write('2/radar/index.html', render_radar_index(posts))]
    for p in projects:
        written.append(write(f'2/projects/{p["slug"]}/index.html', render_project(p, projects)))
    bad = []
    for f in written:
        t = open(f, encoding='utf-8').read()
        if re.search('[–—]', re.sub(r'<script.*?</script>', '', t, flags=re.S)):
            bad.append(('dash', f))
        if t.count('data-l="en"') == 0:
            bad.append(('no twins', f))
    print(f'wrote {len(written)} pages, {len(projects)} projects, {len(posts)} posts', 'PROBLEMS: ' + str(bad) if bad else 'clean')


if __name__ == '__main__':
    main()
