# Buyer variant spec (content/variants/<id>.json)

One JSON file per buyer variant of the homepage. build-home.py renders it into /<path>/index.html: the homepage itself (same design, nav, projects, About, footer links, language switch, English by default; since 2026-09-28 without the film, the Museum and Art Radar) with this file's copy in the sixteen regions `templates/home.html` marks as `<!--variant:NAME-->...<!--/variant:NAME-->`, plus its own value strip (a section the homepage does not have, rendered where the template's empty `<!--variant:value_strip--><!--/variant:value_strip-->` marker sits, right after the black intro block and before the services), its own long section (`guide`, rendered at the empty `<!--variant:guide-->` marker after #what-i-do), its own questions, Advisory rows, footer line and mail subject. Do not write the HTML by hand, and never edit the output folder.

Since 2026-09-28 a variant is indexable and its own canonical, listed once in `sitemap-pages.xml`, with a `Service` and a `BreadcrumbList` beside its FAQPage, and named in llms.txt, agent.txt and answers.md. Since 2026-09-29 (Ron's SEO brief, P1.5) it is linked from every footer's Who I work with column (`site_chrome.WHO_I_WORK_WITH`), from the projects hub, from related pages and the other buyer pages (a variant's own links may name any page but itself), and from the homepage's "Who I work with" section (`#industries`: one tile per variant, from `INDUSTRIES` in `build-home.py`, its line the variant's `intro.line`, its image `images/home2/industries/<id>.webp` from `python3 tools/make_industry_thumbs.py`; a new variant needs an entry there and a thumbnail) and `tools/indexnow.py` pings it like any indexable page. `tools/check_site.py` (the `variants` gate) enforces all of it. The page opens on Ron's agreed main message: `intro.line` is that message verbatim, `intro.statement` the support sentence only, and search wording never goes into the hero, the big line or the statement.

```json
{
  "id": "example-buyer",
  "path": "example-buyer",
  "approved": "Ron 2026-09-27",
  "nav_sub_en": "for example buyers",
  "nav_sub_he": "לקוחות לדוגמה",
  "head": {
    "title": "Example title for one kind of buyer | THEODORA",
    "description": "Example description of what this buyer gets, in one plain sentence of seventy to one hundred sixty five characters.",
    "og_title": "Example share title | THEODORA",
    "og_description": "Example share line."
  },
  "hero": {"l1_en": "An example room.", "l1_he": "חדר לדוגמה.", "l2_en": "Example art.", "l2_he": "אמנות לדוגמה."},
  "intro": {
    "h1_en": "Example h1 that names the service and the place, forty to one hundred ten characters",
    "h1_he": "כותרת לדוגמה שמציינת את השירות ואת המקום",
    "line_en": "An example line.", "line_he": "שורה לדוגמה.",
    "statement_en": "An example statement in Stav's first person voice, sixty to one hundred sixty characters long.",
    "statement_he": "הצהרה לדוגמה בגוף ראשון, בקולה של סתיו."
  },
  "service": {"service_type": "Art consulting and curation for example buyers", "audience": "Example buyers", "area_served": ["New York City", "New Jersey"]},
  "services": [
    {"desc_en": "Example line under the first service", "desc_he": "שורה לדוגמה מתחת לשירות הראשון"},
    {"desc_en": "Example line under the second service", "desc_he": "שורה לדוגמה מתחת לשירות השני"},
    {"desc_en": "Example line under the third service", "desc_he": "שורה לדוגמה מתחת לשירות השלישי"},
    {"desc_en": "Example line under the fourth service", "desc_he": "שורה לדוגמה מתחת לשירות הרביעי"}
  ],
  "value_strip": [
    {"label_en": "An example label.", "label_he": "תווית לדוגמה.", "line_en": "One supporting line for the first column.", "line_he": "שורה תומכת אחת לעמודה הראשונה."},
    {"label_en": "A second label.", "label_he": "תווית שנייה.", "line_en": "One supporting line for the second column.", "line_he": "שורה תומכת אחת לעמודה השנייה."},
    {"label_en": "A third label.", "label_he": "תווית שלישית.", "line_en": "One supporting line for the third column.", "line_he": "שורה תומכת אחת לעמודה השלישית."}
  ],
  "what_i_do": {
    "h2_en": "An example heading for the What I do block.", "h2_he": "כותרת לדוגמה לבלוק מה אני עושה.",
    "p1_en": "Example paragraph, 40 to 160 words, with a link to the <a href=\"/art-curator-new-jersey/\">New Jersey page</a>...",
    "p1_he": "פסקה לדוגמה, עם אותו קישור <a href=\"/art-curator-new-jersey/\">לעמוד ניו ג'רזי</a>...",
    "p2_en": "A second example paragraph, 40 to 160 words...", "p2_he": "פסקה שנייה לדוגמה..."
  },
  "guide": {
    "eyebrow_en": "Step by step", "eyebrow_he": "שלב אחר שלב",
    "h2_en": "An example heading for the long section", "h2_he": "כותרת לדוגמה לחלק הארוך",
    "who_en": "I am Stav Theodor, art curator and advisor, founder of THEODORA in Tenafly, New Jersey. I choose art for example buyers in New York and New Jersey.",
    "who_he": "אני סתיו תאודור, אוצרת ויועצת אמנות...",
    "body_en": "<p>600 to 900 words...</p><h3>A subheading</h3><p>...</p>", "body_he": "<p>...</p>"
  },
  "faq": [
    {"q_en": "An example question a buyer types?", "a_en": "An example answer of 40 to 90 words...", "q_he": "שאלה לדוגמה?", "a_he": "תשובה לדוגמה..."},
    {"home": "Do you work with interior designers and architects?"}
  ],
  "cta_en": "An example closing line for the footer, forty to one hundred forty characters.",
  "cta_he": "שורת סיום לדוגמה לכותרת התחתונה.",
  "mail_subject": "Example subject line"
}
```

The example is shortened (two questions, "..." in the long fields): a real file carries five to seven questions and full paragraphs. Optional objects and fields: `intro.eyebrow_en/_he`, `what_i_do.eyebrow_en/_he`, `advisory` (`h2_en/_he`, `sub_en/_he`), `advisory_rows`, `rooms`, `guides` with its heading and line (its own section below), and `head.og_image` with `head.og_image_alt` (the last two in their own sections below); when one is absent the homepage's own text, rows, rooms or preview image stay.

| Field | Where it shows | Limit |
|---|---|---|
| `id` | the file name, `<id>.json` | a slug: lowercase letters, digits, single hyphens |
| `path` | the address, /<path>/ | one or two slug segments, the last one the id; not a folder of the site or a growth page |
| `approved` | nowhere; who approved the copy and when | `Ron YYYY-MM-DD` or `Stav YYYY-MM-DD` |
| `nav_sub_en`, `nav_sub_he` | the small line under the THEODORA wordmark in the nav ("for hotels", "למלונות"; Ron, 2026-09-29): hidden on the first fold, shown from the second room of the opening, gone once the black intro block enters, never on the homepage (`site_chrome.nav(sub=...)`, `WM_SUB_JS`, `.wm-sub` in `css/theme.css`) | required; at most 32 characters each, lowercase "for ..." in English |
| `head.title`, `head.description` | title and meta description | 30 to 70 and 70 to 160 characters (160 since 2026-09-30) |
| `head.og_title`, `head.og_description` | the share card (Open Graph, Twitter) | at most 70 and 160 |
| `hero.l1`, `hero.l2` | the two lines of the opening | at most 18 characters, in both languages (characters are a proxy; the render check measures pixels at 360px: `node tools/check_render.js` fails a line that ends past the right edge of a 360 by 780 screen, in either language; the homepage's "A beautiful room." ends at about 351) |
| `intro.h1` | the page's h1, the small line in the black intro block | 40 to 110 |
| `intro.line` | the large line ("Art is not an accessory."); on a buyer page Ron's agreed main message, verbatim | at most 60 (wider and balanced on buyer pages) |
| `intro.eyebrow` | the eyebrow above the statement ("What I do") | at most 24 |
| `intro.statement` | the statement | 60 to 160 |
| `services[4].desc` | the line under each of the four service titles (the titles stay) | exactly four, at most 90 each |
| `value_strip[3]` | the value strip, a variant-only section right after the intro block (#intro) and before the services: three columns on desktop, stacked on phones, each a label (serif) and one supporting line | exactly three, required; `label` at most 40, `line` at most 170; plain text, no item repeated |
| `service` | the page's `Service` schema: `service_type` ("Art consulting and curation for law firms"), `audience` (the BusinessAudience), `area_served` (a list from New York City and New Jersey; never Tel Aviv, Ron's SEO brief of 2026-09-29; it names the markets the page targets, never a limit: THEODORA works online with clients anywhere, Ron 2026-09-30, `content/BRIEF.md` section 1); provider is the entity's #org, by `@id` only | required; English only, never shown |
| `guide` | the long section after #what-i-do: `eyebrow`, `h2`, `who` (its first paragraph: the direct answer to "who does this", naming Stav Theodor, also the page's first question) and `body` (h3, p, ul, ol, li, a, em, strong; links as in `what_i_do`, the same set in both languages) | required; eyebrow at most 24, h2 at most 120, who 80 to 260 characters, body 600 to 900 English words, the Hebrew at least 0.6 of that |
| `what_i_do.eyebrow`, `what_i_do.h2` | the eyebrow ("Where I work") and heading of #what-i-do | at most 24 and 120 |
| `what_i_do.p1`, `what_i_do.p2` | its two paragraphs | 40 to 160 English words each, the Hebrew at least 0.6 of that |
| `advisory.h2`, `advisory.sub` | the Advisory heading and the line under it | at most 90 and 200 |
| `advisory_rows` | the Advisory rows | 3 to 8, each a content/pages path (`for-designers`, `advisory/what-does-an-art-advisor-cost`) or `/advisory/` or `/projects/` |
| `faq` | the Questions section and its FAQPage schema | 5 to 7; `{"q_en", "a_en", "q_he", "a_he"}` or `{"home": "<the q_en of a question in content/faq.json>"}`; questions at most 110 characters, ending in "?"; English answers 40 to 90 words, the Hebrew at least 0.6 of that |
| `cta_en`, `cta_he` | the closing line of the footer | 40 to 140 |
| `mail_subject` | the subject of every mail link on the page, the fallback panel's Gmail and Outlook links included | 8 to 60 characters, English, no brackets, different in every variant |
| `compare` | optional: the comparison table (#compare), after the long section and before the guides strip; its own section below | h2 at most 120 and ending in "?", 2 to 8 rows, three columns |
| `handoff` | optional: the who handles what table (#handoff), after #compare; its own section below | h2 at most 120 and ending in "?", 2 to 8 rows, four columns |
| `proof` | optional: named projects, each linking its project page (#proof), after #handoff; its own section below | h2 at most 120 and ending in "?", 1 to 6 items |

Character limits read the English, except the two hero lines, which hold in both languages.

Text rules: every `_en` field has its `_he` twin and the reverse, the Hebrew a faithful translation with Hebrew letters in it; no en or em dashes, no phone number (the business line is added by the shared chrome, never by a variant), no "contact form"; Stav speaks in the first person, "I" (the checker warns on "we", "our" and "us"); no hype words (the list in `tools/check_pages.py`); no fee of Stav's and no $ or % figure at all, industry ranges included (`content/BRIEF.md` section 5, Ron 2026-09-29); facts only from `content/BRIEF.md`. Every field is plain text, written as it should read (`&`, quotes and apostrophes as they are), except `what_i_do.p1` and `p2`, which may use `<a href="...">`, `<em>` and `<strong>`: links go to existing pages (`/advisory/`) or homepage anchors (`#faq`), the English and the Hebrew link to the same set, never to a mailto, a redirect stub or the variant itself (other buyer pages are fine since 2026-09-29). No keys beyond the ones above, none starting with `_`.

The homepage's own copy is the text between the markers in `templates/home.html`: edit it there, keep each marker flush against the element's content, and rebuild. The `value_strip` marker is the one exception: it stays empty and sits flush after the intro's `</section>`, so `index.html` is unchanged (the build fails if anything is put between its two halves). The film (`#film`) is homepage-only: its section sits between `<!--variant:film-->` and `<!--/variant:film-->`, the homepage keeps it byte for byte, and every variant drops it (no flag; Ron, 2026-09-28); the build fails a variant page that still carries `id="film"` or a link to `#film`. A variant changes nothing else (its rooms and preview image aside, below): the build refuses a variant whose About, film, Projects, Museum or Art Radar section differs from the homepage's.

## Its own rooms in the opening (optional)

`rooms` replaces the rooms of the WebGL opening slot by slot: entry 0 is the first fold (the homepage's p3), entries 1 to 3 the three scroll chapters (p4, p5, p1). With a shorter list the opening ends after the variant's last room: the later slots are dropped (no WebGL chapter, no static figure, the scroll spacer shortened to 50vh plus 55vh a chapter), so a buyer page never shows the homepage's residential rooms. `"rooms_rest": "home"` (optional, only beside `rooms`) keeps the homepage's rooms in those slots instead; `"drop"` is the default. Each entry is one room: a before and an after photo of it at the same size, the art placed in the after.

```json
"rooms": [
  {
    "b": "variants/example-buyer/example-buyer_before.webp",
    "a": "variants/example-buyer/example-buyer_after.webp",
    "w": 1800, "h": 1200,
    "rect": [0.5656, 0.1322, 0.7241, 0.5119],
    "fx": 0.6357, "fy": 0.3407,
    "from": "right",
    "cap_en": "Proposal. A conference room with a long walnut table, a large grey canvas on the end wall.",
    "cap_he": "הצעה. חדר ישיבות עם שולחן אגוז ארוך, קנבס אפור גדול על הקיר האחורי.",
    "alt_en": "A conference room with a long walnut table and a large grey canvas on the end wall.",
    "alt_he": "חדר ישיבות עם שולחן אגוז ארוך וקנבס אפור גדול על הקיר האחורי."
  }
]
```

| Field | What it is | Limit |
|---|---|---|
| `b`, `a` | the before and the after image, as paths under `images/home2/` (like `PAIRS` in `js/home-opening.js`) | two different `.webp` files in `images/home2/variants/<id>/` (names in lowercase letters, digits, `-` and `_`), committed with the JSON, 1800 px wide like the homepage's rooms (or the source's own width when it is narrower: never upscaled), encoded with cwebp `-m 6 -sharp_yuv` at q88 stepping down to a q82 floor only to stay under the sanity ceiling of 600 KB (2026-10-06, Ron's image-quality fix; until then a 250 KB cap that pushed rooms down to about q58), neither an image of the homepage's rooms nor of another slot. Optional: a `<name>-2400.webp` twin of both images (the same room and crop, 2400 px wide or the source's width, under 900 KB), made only from a source with real detail past 1800 px; `js/home-opening.js` draws it on fine-pointer screens wider than about 2000 device px and `build-home.py` preloads the matching size |
| `w`, `h` | their size in pixels | both files exactly this size, about 3:2 (w / h from 1.455 to 1.545): a portrait phone draws every room whole in a 3:2 frame |
| `rect` | the artwork in the after image, `[u0, v0, u1, v1]` as fractions of its width and height | inside 0 to 1, u0 < u1, v0 < v1; the wall stroke crosses it and the bloom opens from its centre |
| `fx`, `fy` | the focal point a cover crop keeps (and the static figure's `--fx`, `--fy`) | 0 to 1 |
| `from` | the side of the artwork with more wall, where the brush lands | `"left"` or `"right"` |
| `seed` | optional: the brush texture | a number; absent, the slot keeps the homepage's |
| `cap_en`, `cap_he` | the caption while the room shows (`#cap`), and under the static figure | start `Proposal. ` and `הצעה. `, then describe the room; at most 120 characters in English |
| `alt_en`, `alt_he` | the static figure's alt text (the page writes the English in `alt` and the Hebrew in `data-alt-he`, which the language switch swaps in while Hebrew is on, as the growth pages do; both are required, the `hebrew` gate of `tools/check_site.py` checks) | at most 160 characters in English |

The text rules above apply to the captions and the alt text. `build-home.py` then sets `window.THEODORA_ROOMS` (each room with its slot, numbers at four decimals) in an inline script before the deferred scripts, preloads the first room's two images instead of p3's, and swaps each replaced slot's static figure (image, alt, caption, focal point) and its `#cap` caption, in nine more regions of `templates/home.html`: `room_fig_0` to `room_fig_3`, `room_cap_0` to `room_cap_3`, and `rooms_js`, empty on the homepage. `js/home-opening.js` merges the list into `PAIRS` by slot before anything reads it; the slot keeps its cap key (`p3` and so on), whose text the build has swapped. After the build, `node tools/check_render.js` loads the page at 1280 by 900 and on a 360 by 780 phone: it must request every image of the variant's rooms and get them, request none of the homepage's for a replaced slot, and log no console error.

## Its own link preview (optional)

`head.og_image` and `head.og_image_alt` come together: a 1200 by 630 JPEG under 300 KB, written as its address from the site root, `/images/home2/variants/<id>/<name>.jpg`, and one English line on what it shows (at most 160 characters). They replace `og-home.jpg` and its description in og:image, og:image:alt and twitter:image, for this variant only. Link previews are cached: after a change, re-scrape the page in the Facebook Sharing Debugger and the LinkedIn Post Inspector.

## Its guides (optional, 2026-09-29)

`guides` lists 1 to 6 guide pages (`"guide/<slug>"`, each a content/pages guide that is built) in display order. The page then shows a Guides strip (`#guides`, variant only, after the long section #guide and before #about; the template's `<!--variant:guides--><!--/variant:guides-->` marker stays empty, so the homepage never has it): the eyebrow Guides, the heading `guides_heading_en`/`guides_heading_he` (at most 90 characters; required when `guides` is set, and it may be stored before the guides exist; the safety-net fallback is "The answers in more detail"; write it for the page, "Guides for law firms"), an optional line `guides_sub_en`/`guides_sub_he` (at most 200), the "All guides" arrow to the guides index /guide/, and one card per guide (its title, `dek_en` or its lead's first sentence, its hero diagram, or its after image marked Proposal). The heading and line fields exist only beside `guides`. `tools/check_variants.py` check p.

## Its comparison, who handles what and proof (optional, 2026-10-10)

Three more optional fields (Ron's plan, 2026-10-10: added beside what the page has, nothing in it changed). Each renders as its own variant-only section after the long section (#guide) and before the guides strip (#guides), in this order: `compare` (#compare), `handoff` (#handoff), `proof` (#proof). The template's `<!--variant:compare--><!--/variant:compare-->`, `<!--variant:handoff--><!--/variant:handoff-->` and `<!--variant:proof--><!--/variant:proof-->` markers stay empty, so the homepage never has them and a variant without a field renders exactly as before. Never at the top of the page: the opening stays Ron's agreed message (AGENTS.md Section 3.9). The tables use the guides' table markup (`figure.tbl` in the reading column `.prose.guide`, css/theme.css 5.6: hairline rows, a small caps header, the first column as the row header, a sideways scroll on a phone), one table per language.

```json
"compare": {
  "eyebrow_en": "Before you decide", "eyebrow_he": "לפני שמחליטים",
  "h2_en": "How do law firms usually get art, and what does a curator change?",
  "h2_he": "איך משרדי עורכי דין משיגים בדרך כלל אמנות, ומה אוצרת משנה?",
  "intro_en": "One or two sentences that answer the question.", "intro_he": "משפט או שניים שעונים על השאלה.",
  "cols": {"aspect_en": "Aspect", "aspect_he": "היבט", "usual_en": "The usual way", "usual_he": "הדרך המקובלת",
           "curator_en": "With a curator", "curator_he": "עם אוצרת"},
  "rows": [{"aspect_en": "Representation", "aspect_he": "ייצוג",
            "usual_en": "A gallery represents its artists, and that is its job", "usual_he": "גלריה מייצגת את האמנים שלה, וזה התפקיד שלה",
            "curator_en": "I represent the firm, with no closed roster, so I can reach out to any artist in the world",
            "curator_he": "אני מייצגת את המשרד, בלי רשימה סגורה של אמנים, ולכן אני יכולה לפנות לכל אמן בעולם"}]
},
"handoff": {
  "eyebrow_en": "Start to finish", "eyebrow_he": "מההתחלה ועד הסוף",
  "h2_en": "Who handles what in a law firm's art project, from the first conversation to installation?",
  "h2_he": "מי אחראי על מה בפרויקט האמנות של משרד עורכי דין, מהשיחה הראשונה ועד ההתקנה?",
  "cols": {"step_en": "Step", "step_he": "שלב", "what_en": "What happens", "what_he": "מה קורה",
           "who_en": "Who handles it", "who_he": "מי אחראי", "order_en": "Order", "order_he": "סדר"},
  "rows": [{"step_en": "Research", "step_he": "מחקר",
            "what_en": "I look for works and artists through my network, and assess the market value of each work.",
            "what_he": "אני מחפשת יצירות ואמנים דרך הרשת שלי, ומעריכה את שווי השוק של כל יצירה.",
            "who_en": "I do", "who_he": "אני", "order_en": "Second", "order_he": "שני"}]
},
"proof": {
  "eyebrow_en": "Hospitality", "eyebrow_he": "אירוח",
  "h2_en": "Where can you see my hospitality work?", "h2_he": "איפה אפשר לראות את העבודה שלי בתחום האירוח?",
  "line_en": "Concepts and collections built while collaborating with luxury hospitality leaders.",
  "line_he": "קונספטים ואוספים שנבנו בשיתוף פעולה עם מובילים בתחום האירוח היוקרתי.",
  "items": [{"name_en": "Waldorf Astoria Chengdu", "name_he": "וולדורף אסטוריה צ'נגדו",
             "line_en": "China. Sculptural works for the lobby.", "line_he": "סין. עבודות פיסוליות ללובי.",
             "href": "/projects/hotels-and-hospitality-collections/", "img": "/images/projects/waldorf-lobby.jpg"}]
}
```

| Field | What it is | Limit |
|---|---|---|
| `compare.h2`, `handoff.h2`, `proof.h2` | the section's heading, phrased as the buyer's own question | required; at most 120 characters, ending in "?" in both languages |
| `*.eyebrow` | the small line above the heading | optional; at most 24 |
| `compare.intro`, `handoff.intro` | one opening paragraph above the table, the direct answer | optional; at most 320 |
| `compare.cols`, `compare.rows` | the header cells and the rows of the table aspect, the usual way, with a curator (`aspect`, `usual`, `curator`, each `_en` and `_he`) | required beside compare; 2 to 8 rows, every cell filled in both languages, a header cell at most 40 and a body cell at most 240 |
| `handoff.cols`, `handoff.rows` | the same for step, what happens, who handles it, order (`step`, `what`, `who`, `order`) | required beside handoff; 2 to 8 rows, the same cell limits |
| `proof.line` | the line under the heading | required beside proof; at most 200 |
| `proof.items` | one card each: `name` (the project, as text), `line` (what was done, in the project's own published wording), `href` (its project page) and optional `img` | 1 to 6; name at most 60, line at most 120; `href` a built `/projects/<slug>/` page from content/pages; `img` a photograph that page already shows (its hero_image or a figure in its body), whose alt twins the build reads from that page; no image is better than a borrowed one |

A table never has more than four columns (`TABLE_MAX_COLS` in build-home.py and tools/check_variants.py). Text rules as everywhere above, and these: the usual ways come from the buyer research and are described fairly, never by a competitor's name (no ArtLink); the curator column tells the value story (`content/BRIEF.md` section 5: in most cases a better price than at a large auction or through a gallery, the service included, a curator who represents the client and is open to any artist), with no fee, commission, percentage, dollar figure or number about price; leasing appears only as the alternative, never as Stav's service; the handoff rows use only `content/BRIEF.md` facts (its process steps in section 4 and section 4a: her own installation team, the certificate of insurance that can name the landlord or managing agent, installation after hours), with no durations or week counts. `python3 tools/check_variants.py` (check q) fails a heading without "?", a fifth column, a missing cell or twin, a proof link that is not a built project page, and a proof photo the project page does not show; its text gates (dashes, phone, fee, hype, "contact form", Hebrew letters) cover every heading, line and cell of the three blocks.

## Paths, deleting, validating

Changing a variant's `path` leaves the old folder behind; `python3 build.py` then fails the `variants` gate ("stale variant folder? git rm -r <folder>") until it is removed. Deleting a variant: `git rm` the JSON, the folder and its images, `images/home2/variants/<id>/`.

Validate before you hand off, a draft anywhere on disk included (name it `<id>.json`; the image paths in it are read from the repo):

```
python3 tools/check_variants.py content/variants/<id>.json
python3 tools/check_variants.py /any/folder/<id>.json
```

It must print OK (warnings do not fail). Then `python3 build.py` renders every variant and runs the gates.
