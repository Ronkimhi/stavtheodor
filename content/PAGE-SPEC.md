# Page JSON spec (content/pages/<slug>.json)

One JSON file per page. build-site-pages.py renders it into /<path>/index.html with the site's nav, style, language switch (English by default on every page since 2026-09-26, Hebrew when the visitor picks it, remembered site-wide), FAQ schema, breadcrumb schema and footer. Do not write HTML pages by hand.

```json
{
  "path": "advisory/what-does-an-art-advisor-cost",
  "section": "advisory",
  "kicker": "Art advisory",
  "title_en": "What does an art advisor cost?",
  "title_he": "כמה עולה יועצת אמנות?",
  "meta_description": "Under 160 characters. The direct answer, in English, for search and LLM snippets.",
  "lead_en": "One or two sentences that answer the question outright. Plain text, no HTML.",
  "lead_he": "Faithful Hebrew translation of the lead.",
  "before_after": "restaurants",
  "body_en": "<p>...</p><h2>...</h2><p>...</p>",
  "body_he": "<p>...</p><h2>...</h2><p>...</p>",
  "faq": [{"q_en": "...", "a_en": "...", "q_he": "...", "a_he": "..."}],
  "schema_type": "Service",
  "service_type": "Art advisory for private residences",
  "cta_en": "optional override of the closing call to action",
  "cta_he": "optional",
  "related": ["advisory/how-the-art-advisory-process-works", "projects/closter-new-jersey-new-construction"],
  "og_image": "/images/spaces/restaurants_og.jpg",
  "date": "2026-09-04"
}
```

Sections and paths: `advisory/<slug>` (schema_type Service or Article), `projects/<slug>` (schema_type CreativeWork or Article; a `hero_image` that is a real photograph of that same project, or, when there is none, `place_en` and `place_he`, the place name its typographic hero card shows; never another project's photo and never a before/after), `for-designers`, `for-brokers`, `for-advisors` (section "partners", schema_type Service), `guide/<slug>` (section "guide", schema_type Article), and the two local landing pages `art-curator-new-jersey`, `art-curator-new-york` (section "local", schema_type Service, 1,100 to 1,900 English words, "art curator" in title_en and lead_en, breadcrumb under /advisory/, listed first on the advisory hub and in the homepage Advisory rows).

The hero of an article page (advisory, local, partners, guide) is `before_after`, a key of `content/spaces.json` (added 2026-09-28): a pixel-aligned pair in `images/spaces/<key>_before.webp` and `_after.webp` (1800 px, with 1000 px twins `-1000.webp`) and a 1200 by 630 `<key>_og.jpg` for `og_image`. The spaces are AI-rendered with real catalog artworks placed on the wall, so the build labels every one "Proposal · how THEODORA would dress this space" and captions it from `spaces.json`, whose captions say "space", never "room". With JavaScript and motion allowed the figure pins for about 120vh while the after is brushed over the before (`js/before-after.js`, `.ba` in `css/theme.css`); otherwise it is a still pair. A page may use `hero_image` instead, for a real photograph. Give neighbouring pages different pairs.

Optional fields: `head_title` (the page's `<title>` before " · THEODORA" when it should differ from the h1, `title_en`; at most 60 characters with the suffix; Ron's SEO brief of 2026-09-29, P1.4 and P1.5), `radar_posts` (a list of Art Radar slugs for the "From Art Radar" block every article page carries; without it the three newest posts show; every slug must exist in content/posts.html), `area_served` (a list of schema.org Place objects for Service pages; the default is New York City, New Jersey, Tel Aviv). Never promise a "contact form": there is none. Point people to `stav@stavtheodor.com` and to "the contact details at the end of this page" linking `#contact` (Hebrew: "פרטי יצירת הקשר בסוף העמוד").

Body HTML rules: p, h2, h3, ul, ol, li, strong, em, a, blockquote, figure, img, figcaption only. Root relative image paths. Links to other pages of this set use `/advisory/<slug>/` style absolute paths. No inline styles, no classes, no scripts.

No internal notes in a page JSON. Every file under `content/` is served publicly exactly as it is in the repo (for example https://stavtheodor.com/content/pages/for-designers.json), so a key named `editor_note`, or any key starting with `_` or `note` (any case), at any depth, fails `tools/check_pages.py`, which `build-site-pages.py` runs on every page before writing anything, so `python3 build.py` stops. Internal notes, decisions and open questions go to the site owner's private system: `the-system-v8-ron/B-brain/06-deliverables/theodora-growth/decisions-for-stav.md` in the private ron-brain repo.

Validate before you hand off: `python3 tools/check_pages.py content/pages/<slug>.json` must print OK.
