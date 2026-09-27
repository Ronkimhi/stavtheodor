# Buyer variant spec (content/variants/<id>.json)

One JSON file per buyer variant of the homepage. build-home.py renders it into /<path>/index.html: the homepage itself (same design, nav, projects, About, film, Museum, Art Radar, footer links, language switch, English by default) with this file's copy in the sixteen regions `templates/home.html` marks as `<!--variant:NAME-->...<!--/variant:NAME-->`, plus its own questions, Advisory rows, footer line and mail subject. Do not write the HTML by hand, and never edit the output folder.

A variant is noindex and its own canonical. It is in no sitemap, in none of llms.txt, agent.txt, answers.md and robots.txt, linked from no other page and never sent to IndexNow. `tools/check_site.py` (the `variants` gate) and `tools/indexnow.py` enforce that.

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
  "services": [
    {"desc_en": "Example line under the first service", "desc_he": "שורה לדוגמה מתחת לשירות הראשון"},
    {"desc_en": "Example line under the second service", "desc_he": "שורה לדוגמה מתחת לשירות השני"},
    {"desc_en": "Example line under the third service", "desc_he": "שורה לדוגמה מתחת לשירות השלישי"},
    {"desc_en": "Example line under the fourth service", "desc_he": "שורה לדוגמה מתחת לשירות הרביעי"}
  ],
  "what_i_do": {
    "h2_en": "An example heading for the What I do block.", "h2_he": "כותרת לדוגמה לבלוק מה אני עושה.",
    "p1_en": "Example paragraph, 40 to 160 words, with a link to the <a href=\"/art-curator-new-jersey/\">New Jersey page</a>...",
    "p1_he": "פסקה לדוגמה, עם אותו קישור <a href=\"/art-curator-new-jersey/\">לעמוד ניו ג'רזי</a>...",
    "p2_en": "A second example paragraph, 40 to 160 words...", "p2_he": "פסקה שנייה לדוגמה..."
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

The example is shortened (two questions, "..." in the long fields): a real file carries five to seven questions and full paragraphs. Optional objects and fields: `intro.eyebrow_en/_he`, `what_i_do.eyebrow_en/_he`, `advisory` (`h2_en/_he`, `sub_en/_he`) and `advisory_rows`; when one is absent the homepage's own text or rows stay.

| Field | Where it shows | Limit |
|---|---|---|
| `id` | the file name, `<id>.json` | a slug: lowercase letters, digits, single hyphens |
| `path` | the address, /<path>/ | one or two slug segments, the last one the id; not a folder of the site or a growth page |
| `approved` | nowhere; who approved the copy and when | `Ron YYYY-MM-DD` or `Stav YYYY-MM-DD` |
| `head.title`, `head.description` | title and meta description | 30 to 70 and 70 to 165 characters |
| `head.og_title`, `head.og_description` | the share card (Open Graph, Twitter) | at most 70 and 160 |
| `hero.l1`, `hero.l2` | the two lines of the opening | at most 18 characters, in both languages |
| `intro.h1` | the page's h1, the small line in the black intro block | 40 to 110 |
| `intro.line` | the large line under it ("Art is not an accessory.") | at most 32 |
| `intro.eyebrow` | the eyebrow above the statement ("What I do") | at most 24 |
| `intro.statement` | the statement | 60 to 160 |
| `services[4].desc` | the line under each of the four service titles (the titles stay) | exactly four, at most 90 each |
| `what_i_do.eyebrow`, `what_i_do.h2` | the eyebrow ("Where I work") and heading of #what-i-do | at most 24 and 120 |
| `what_i_do.p1`, `what_i_do.p2` | its two paragraphs | 40 to 160 English words each, the Hebrew at least 0.6 of that |
| `advisory.h2`, `advisory.sub` | the Advisory heading and the line under it | at most 90 and 200 |
| `advisory_rows` | the Advisory rows | 3 to 8, each a content/pages path (`for-designers`, `advisory/what-does-an-art-advisor-cost`) or `/advisory/` or `/projects/` |
| `faq` | the Questions section and its FAQPage schema | 5 to 7; `{"q_en", "a_en", "q_he", "a_he"}` or `{"home": "<the q_en of a question in content/faq.json>"}`; questions at most 110 characters, ending in "?"; English answers 40 to 90 words, the Hebrew at least 0.6 of that |
| `cta_en`, `cta_he` | the closing line of the footer | 40 to 140 |
| `mail_subject` | the subject of every mail link on the page, the fallback panel's Gmail and Outlook links included | 8 to 60 characters, English, no brackets, different in every variant |

Character limits read the English, except the two hero lines, which hold in both languages.

Text rules: every `_en` field has its `_he` twin and the reverse, the Hebrew a faithful translation with Hebrew letters in it; no en or em dashes, no phone number, no "contact form"; Stav speaks in the first person, "I" (the checker warns on "we", "our" and "us"); no hype words (the list in `tools/check_pages.py`); no fee of Stav's, and a $ or % figure only with the word "industry" (`content/BRIEF.md` section 5); facts only from `content/BRIEF.md`. Every field is plain text, written as it should read (`&`, quotes and apostrophes as they are), except `what_i_do.p1` and `p2`, which may use `<a href="...">`, `<em>` and `<strong>`: links go to existing pages (`/advisory/`) or homepage anchors (`#faq`), the English and the Hebrew link to the same set, never to a mailto, a redirect stub or another variant. No keys beyond the ones above, none starting with `_`.

The homepage's own copy is the text between the markers in `templates/home.html`: edit it there, keep each marker flush against the element's content, and rebuild. A variant changes nothing else: the build refuses a variant whose About, film, Projects, Museum or Art Radar section differs from the homepage's.

Changing a variant's `path` leaves the old folder behind; `python3 build.py` then fails the `variants` gate ("stale variant folder? git rm -r <folder>") until it is removed. Deleting a variant: `git rm` the JSON and the folder.

Validate before you hand off, a draft anywhere on disk included (name it `<id>.json`):

```
python3 tools/check_variants.py content/variants/<id>.json
python3 tools/check_variants.py /any/folder/<id>.json
```

It must print OK (warnings do not fail). Then `python3 build.py` renders every variant and runs the gates.
