# stavtheodor.com

**Read `AGENTS.md` in this directory in full before making any change.** It is the single source of truth for this repo (multi-AI sync protocol, the site owner's standing content rules including the mandatory bilingual posts, workflow, and the shared Work Log you must append to). `ADD-BLOG-POST-GUIDE.md` has the detailed post templates.

---

## How the site is built (since 2026-09-26)

Every page is generated. No framework, no npm: three Python scripts, one shared module, one stylesheet.

| You edit | The build writes |
|---|---|
| `content/posts.html` (every Art Radar post, newest first) | `radar/<slug>/index.html`, `radar/index.html`, the homepage timeline, `sitemap.xml` |
| `content/pages/*.json` (advisory, projects, partners, guide) | `advisory/`, `projects/`, `for-*/`, `guide/` pages and the two hubs, the homepage project cards and advisory rows |
| `content/variants/*.json` (buyer variants of the homepage, format `content/VARIANT-SPEC.md`) | one indexable copy of the homepage per file at `/<path>/` (since 2026-09-28, Ron), with its own copy in the marked regions, questions and mail subject; its own canonical, listed in `sitemap-pages.xml`, linked only from the homepage's `#industries` section |
| `content/faq.json` | the homepage FAQ and its FAQPage schema (the same text, by construction) |
| `content/entity.json` | the Person + ProfessionalService + WebSite JSON-LD on every page |
| `templates/home.html` | `index.html` (the approved homepage design, with slots) |
| `site_chrome.py` | the nav, footer, language switch, mailto fallback, GA tag and `<head>` of every page |
| `css/theme.css` | the one theme every page links |
| `js/home-opening.js`, `js/home-scroll.js` | the homepage opening (WebGL brush) and smooth wheel |
| `js/vendor/` | GSAP 3.13 (core, ScrollTrigger, SplitText) and Lenis 1.3.11, vendored with their licences, loaded with defer |
| `fonts/` | the three font families as woff2 (latin, latin-ext, hebrew subsets), declared at the top of `css/theme.css` |

One command, from the repo root:

```
python3 build.py
```

It runs `build-site-pages.py` (which runs `build-post-pages.py`), then `tools/check_variants.py` (the buyer variants' JSON), then `build-home.py` (the homepage, the redirect stubs and the variant pages), then `tools/build_sitemap.py` (the sitemap index and its three children), then the gates in `tools/check_site.py` (dashes, phone numbers, language twins, anchors, internal links, JSON-LD, FAQ mirror, noindex, removed assets, language default, sitemap, variants). Never hand-edit a generated file: `index.html`, `radar/`, `advisory/`, `projects/`, `for-*/`, `guide/`, `2/` (redirect stubs), the buyer variant folders and `sitemap.xml` are all rewritten by the build.

---

## Hosting: GitHub Pages (migrated from Netlify 2026-06-30)

The site is served from the `Ronkimhi/stavtheodor` GitHub repo via GitHub Pages, with `stavtheodor.com` (apex + `www`) pointed at it via `CNAME` and GoDaddy DNS. Pushing to `main` deploys automatically, no manual deploy step.

**Deploying a change:** `python3 build.py`, then `git add`, `git commit`, `git push origin main`. GitHub Pages picks it up within a minute or two (CDN cache about 10 minutes).

---

## Adding a new post (the dual-publish flow)

**Full step-by-step instructions, exact templates, and a copy-paste checklist:** see [`ADD-BLOG-POST-GUIDE.md`](ADD-BLOG-POST-GUIDE.md) in this repo, written to be handed to any AI agent with no other context needed.

Every post goes to both channels:

1. Publish in the WhatsApp group as usual
2. Paste the final version to Claude: *"Here's the final version I published: [paste]"*
3. Claude will:
   - Save it to `B-brain/04-published/01-whatsapp/YYYY-MM-DD-[slug].md` (Published Posts Protocol)
   - Add it to `content/posts.html` at the **top**, right under the `POST TEMPLATE` comment. Never to `index.html`: it is generated, and the build refuses to run while a post is in it.
4. Run `python3 build.py`. This regenerates the post's own page `radar/<slug>/index.html`, the archive `radar/index.html`, the homepage (its timeline shows the six newest posts), and `sitemap.xml`, and points the post's JSON-LD `url` / `mainEntityOfPage` at its real permalink.
5. **Update `llms.txt` and `answers.md` by hand.** The build does not touch them, and `agent.txt` (a short fact sheet) has no post list. Use the real `/radar/<slug>/` permalink, never a `#slug` anchor. These are what AI crawlers read to cite the site.
6. Commit and push (see Hosting above)

## Adding photos to a post

Send Claude the image file(s) and say which post they belong to. They get optimized into `images/` (max 900px, JPEG about 72 quality, named `YYYY-MM-DD-[slug].jpg`) and referenced from the post, with a quiet caption. The page is designed to look finished with or without them.

## The homepage

The homepage is the design approved on 2026-09-26 (near-black ground, a WebGL brush opening over four rooms, one serif line per screen, the film, six projects, the advisory rows, the Museum, the six newest posts, the seven questions). Its markup lives in `templates/home.html`; the opening's before and after photos are `images/home2/pairs/`; the film is `videos/theodora-film-2026-09-26.mp4` (67 seconds). To change the copy, edit the template and rebuild. The old portfolio slideshow is gone.

Sixteen regions of the template (the hero lines, the h1, the intro, the service lines, the What I do block, the Advisory heading) sit between `<!--variant:NAME-->` markers: the homepage keeps the text between them, and each buyer variant (`content/variants/<id>.json`, AGENTS.md Section 3.9) replaces it at its own indexable address.

## Media notes

- Post images live in `images/`, project photos in `images/projects/`, homepage photos in `images/home2/`.
- The original WhatsApp media export (including the raw chat file, which contains member phone numbers and must NEVER be deployed or shared) lives outside this repo at `B-brain/04-published/01-whatsapp/media-export-2026-06-12/`.
- `og-image.jpg` is the social share card. `favicon.svg` / `favicon-32.png` / `apple-touch-icon.png` are the browser-tab and home-screen icons. All are referenced by absolute URL, so if the site is ever renamed from `stavtheodor.com`, those URLs must be updated to match.
