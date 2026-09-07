# Page JSON spec (content/pages/<slug>.json)

One JSON file per page. build-site-pages.py renders it into /<path>/index.html with the site's nav, style, language toggle (Hebrew default, English on toggle), FAQ schema, breadcrumb schema and footer. Do not write HTML pages by hand.

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
  "hero_image": {"src": "/images/projects/closter-dining.jpg", "alt_en": "Dining room in Closter, New Jersey, three paintings above the table", "alt_he": "...", "caption_en": "Closter, New Jersey. New construction, collection curated with New York galleries.", "caption_he": "..."},
  "body_en": "<p>...</p><h2>...</h2><p>...</p>",
  "body_he": "<p>...</p><h2>...</h2><p>...</p>",
  "faq": [{"q_en": "...", "a_en": "...", "q_he": "...", "a_he": "..."}],
  "schema_type": "Service",
  "service_type": "Art advisory for private residences",
  "cta_en": "optional override of the closing call to action",
  "cta_he": "optional",
  "related": ["advisory/how-the-art-advisory-process-works", "projects/closter-new-jersey-new-construction"],
  "og_image": "/images/projects/closter-dining.jpg",
  "date": "2026-09-04"
}
```

Sections and paths: `advisory/<slug>` (schema_type Service or Article), `projects/<slug>` (schema_type CreativeWork or Article, hero_image required), `for-designers`, `for-brokers`, `for-advisors` (section "partners", schema_type Service), `guide/<slug>` (section "guide", schema_type Article).

Body HTML rules: p, h2, h3, ul, ol, li, strong, em, a, blockquote, figure, img, figcaption only. Root relative image paths. Links to other pages of this set use `/advisory/<slug>/` style absolute paths. No inline styles, no classes, no scripts.

Validate before you hand off: `python3 tools/check_pages.py content/pages/<slug>.json` must print OK.
