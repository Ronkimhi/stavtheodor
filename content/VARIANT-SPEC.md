# Buyer variant spec (content/variants/<id>.json)

One JSON file per buyer variant of the homepage. build-home.py renders it into /<path>/index.html: the homepage itself (same design, nav, projects, About, footer links, language switch, English by default; since 2026-09-28 without the film, the Museum and Art Radar) with this file's copy in the sixteen regions `templates/home.html` marks as `<!--variant:NAME-->...<!--/variant:NAME-->`, plus its own value strip (a section the homepage does not have, rendered where the template's empty `<!--variant:value_strip--><!--/variant:value_strip-->` marker sits, right after the black intro block and before the services), its own long section (`guide`, rendered at the empty `<!--variant:guide-->` marker after #what-i-do), its own questions, Advisory rows, footer line and mail subject. Do not write the HTML by hand, and never edit the output folder.

Since 2026-09-28 a variant is indexable and its own canonical, listed once in `sitemap-pages.xml`, with a `Service` and a `BreadcrumbList` beside its FAQPage, and named in llms.txt, agent.txt and answers.md. It is linked only from its paired pages (`VARIANT_LINKERS` in `tools/check_site.py`) and from the homepage's "Who I work with" section (`#industries`: one tile per variant, from `INDUSTRIES` in `build-home.py`, its line the variant's `intro.line`, its image `images/home2/industries/<id>.webp` from `python3 tools/make_industry_thumbs.py`; a new variant needs an entry there and a thumbnail) and `tools/indexnow.py` pings it like any indexable page. `tools/check_site.py` (the `variants` gate) enforces all of it. The page opens on Ron's agreed main message: `intro.line` is that message verbatim, `intro.statement` the support sentence only, and search wording never goes into the hero, the big line or the statement.

```json
{
  "id": "example-buyer",
  "path": "example-buyer",
  "approved": "Ron 2026-09-27",
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

The example is shortened (two questions, "..." in the long fields): a real file carries five to seven questions and full paragraphs. Optional objects and fields: `intro.eyebrow_en/_he`, `what_i_do.eyebrow_en/_he`, `advisory` (`h2_en/_he`, `sub_en/_he`), `advisory_rows`, `rooms`, and `head.og_image` with `head.og_image_alt` (the last two in their own sections below); when one is absent the homepage's own text, rows, rooms or preview image stay.

| Field | Where it shows | Limit |
|---|---|---|
| `id` | the file name, `<id>.json` | a slug: lowercase letters, digits, single hyphens |
| `path` | the address, /<path>/ | one or two slug segments, the last one the id; not a folder of the site or a growth page |
| `approved` | nowhere; who approved the copy and when | `Ron YYYY-MM-DD` or `Stav YYYY-MM-DD` |
| `head.title`, `head.description` | title and meta description | 30 to 70 and 70 to 165 characters |
| `head.og_title`, `head.og_description` | the share card (Open Graph, Twitter) | at most 70 and 160 |
| `hero.l1`, `hero.l2` | the two lines of the opening | at most 18 characters, in both languages (characters are a proxy; the render check measures pixels at 360px: `node tools/check_render.js` fails a line that ends past the right edge of a 360 by 780 screen, in either language; the homepage's "A beautiful room." ends at about 351) |
| `intro.h1` | the page's h1, the small line in the black intro block | 40 to 110 |
| `intro.line` | the large line ("Art is not an accessory."); on a buyer page Ron's agreed main message, verbatim | at most 60 (wider and balanced on buyer pages) |
| `intro.eyebrow` | the eyebrow above the statement ("What I do") | at most 24 |
| `intro.statement` | the statement | 60 to 160 |
| `services[4].desc` | the line under each of the four service titles (the titles stay) | exactly four, at most 90 each |
| `value_strip[3]` | the value strip, a variant-only section right after the intro block (#intro) and before the services: three columns on desktop, stacked on phones, each a label (serif) and one supporting line | exactly three, required; `label` at most 40, `line` at most 170; plain text, no item repeated |
| `service` | the page's `Service` schema: `service_type` ("Art consulting and curation for law firms"), `audience` (the BusinessAudience), `area_served` (a list from New York City and New Jersey; never Tel Aviv, Ron's SEO brief of 2026-09-29); provider is the entity's #org, by `@id` only | required; English only, never shown |
| `guide` | the long section after #what-i-do: `eyebrow`, `h2`, `who` (its first paragraph: the direct answer to "who does this", naming Stav Theodor, also the page's first question) and `body` (h3, p, ul, ol, li, a, em, strong; links as in `what_i_do`, the same set in both languages) | required; eyebrow at most 24, h2 at most 120, who 80 to 260 characters, body 600 to 900 English words, the Hebrew at least 0.6 of that |
| `what_i_do.eyebrow`, `what_i_do.h2` | the eyebrow ("Where I work") and heading of #what-i-do | at most 24 and 120 |
| `what_i_do.p1`, `what_i_do.p2` | its two paragraphs | 40 to 160 English words each, the Hebrew at least 0.6 of that |
| `advisory.h2`, `advisory.sub` | the Advisory heading and the line under it | at most 90 and 200 |
| `advisory_rows` | the Advisory rows | 3 to 8, each a content/pages path (`for-designers`, `advisory/what-does-an-art-advisor-cost`) or `/advisory/` or `/projects/` |
| `faq` | the Questions section and its FAQPage schema | 5 to 7; `{"q_en", "a_en", "q_he", "a_he"}` or `{"home": "<the q_en of a question in content/faq.json>"}`; questions at most 110 characters, ending in "?"; English answers 40 to 90 words, the Hebrew at least 0.6 of that |
| `cta_en`, `cta_he` | the closing line of the footer | 40 to 140 |
| `mail_subject` | the subject of every mail link on the page, the fallback panel's Gmail and Outlook links included | 8 to 60 characters, English, no brackets, different in every variant |

Character limits read the English, except the two hero lines, which hold in both languages.

Text rules: every `_en` field has its `_he` twin and the reverse, the Hebrew a faithful translation with Hebrew letters in it; no en or em dashes, no phone number (the business line is added by the shared chrome, never by a variant), no "contact form"; Stav speaks in the first person, "I" (the checker warns on "we", "our" and "us"); no hype words (the list in `tools/check_pages.py`); no fee of Stav's, and a $ or % figure only with the word "industry" (`content/BRIEF.md` section 5); facts only from `content/BRIEF.md`. Every field is plain text, written as it should read (`&`, quotes and apostrophes as they are), except `what_i_do.p1` and `p2`, which may use `<a href="...">`, `<em>` and `<strong>`: links go to existing pages (`/advisory/`) or homepage anchors (`#faq`), the English and the Hebrew link to the same set, never to a mailto, a redirect stub or another variant. No keys beyond the ones above, none starting with `_`.

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
| `b`, `a` | the before and the after image, as paths under `images/home2/` (like `PAIRS` in `js/home-opening.js`) | two different `.webp` files in `images/home2/variants/<id>/` (names in lowercase letters, digits, `-` and `_`), committed with the JSON, each under 250 KB (1800 px wide, like the homepage's rooms), neither an image of the homepage's rooms nor of another slot |
| `w`, `h` | their size in pixels | both files exactly this size, about 3:2 (w / h from 1.455 to 1.545): a portrait phone draws every room whole in a 3:2 frame |
| `rect` | the artwork in the after image, `[u0, v0, u1, v1]` as fractions of its width and height | inside 0 to 1, u0 < u1, v0 < v1; the wall stroke crosses it and the bloom opens from its centre |
| `fx`, `fy` | the focal point a cover crop keeps (and the static figure's `--fx`, `--fy`) | 0 to 1 |
| `from` | the side of the artwork with more wall, where the brush lands | `"left"` or `"right"` |
| `seed` | optional: the brush texture | a number; absent, the slot keeps the homepage's |
| `cap_en`, `cap_he` | the caption while the room shows (`#cap`), and under the static figure | start `Proposal. ` and `הצעה. `, then describe the room; at most 120 characters in English |
| `alt_en`, `alt_he` | the static figure's alt text (the page writes the English, as the growth pages do) | at most 160 characters in English |

The text rules above apply to the captions and the alt text. `build-home.py` then sets `window.THEODORA_ROOMS` (each room with its slot, numbers at four decimals) in an inline script before the deferred scripts, preloads the first room's two images instead of p3's, and swaps each replaced slot's static figure (image, alt, caption, focal point) and its `#cap` caption, in nine more regions of `templates/home.html`: `room_fig_0` to `room_fig_3`, `room_cap_0` to `room_cap_3`, and `rooms_js`, empty on the homepage. `js/home-opening.js` merges the list into `PAIRS` by slot before anything reads it; the slot keeps its cap key (`p3` and so on), whose text the build has swapped. After the build, `node tools/check_render.js` loads the page at 1280 by 900 and on a 360 by 780 phone: it must request every image of the variant's rooms and get them, request none of the homepage's for a replaced slot, and log no console error.

## Its own link preview (optional)

`head.og_image` and `head.og_image_alt` come together: a 1200 by 630 JPEG under 300 KB, written as its address from the site root, `/images/home2/variants/<id>/<name>.jpg`, and one English line on what it shows (at most 160 characters). They replace `og-home.jpg` and its description in og:image, og:image:alt and twitter:image, for this variant only. Link previews are cached: after a change, re-scrape the page in the Facebook Sharing Debugger and the LinkedIn Post Inspector.

## Paths, deleting, validating

Changing a variant's `path` leaves the old folder behind; `python3 build.py` then fails the `variants` gate ("stale variant folder? git rm -r <folder>") until it is removed. Deleting a variant: `git rm` the JSON, the folder and its images, `images/home2/variants/<id>/`.

Validate before you hand off, a draft anywhere on disk included (name it `<id>.json`; the image paths in it are read from the repo):

```
python3 tools/check_variants.py content/variants/<id>.json
python3 tools/check_variants.py /any/folder/<id>.json
```

It must print OK (warnings do not fail). Then `python3 build.py` renders every variant and runs the gates.
